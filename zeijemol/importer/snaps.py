##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import print_function
import os
import glob
import sys
import hashlib
import json
import re

# Cubicweb import
from cubicweb import cwconfig
from cubicweb.dbapi import in_memory_repo_cnx
from cubicweb import Binary
from cubicweb.server.utils import crypt_password

# SnapView import
from zeijemol.docgen.rst2html import rst2html


class SnapsImporter(object):
    """ This class enables us to add new snaps in CW instance.

    Notes
    -----
    Here is an example of the definition of the 'relations' parameter:

    ::

        relations = [
            ("CWUser", "in_group", "CWGroup")
        ]
    """
    def __init__(self, instance_name, login, password):
        """ Initialize the SeniorData class.

        Parameters
        ----------
        instance_name: str
            the name of the cubicweb instance based in the 'snapview' cube.
        login: str
            a login.
        password: str
            the corresponding password.
        """
        # Create a cw session
        config = cwconfig.instance_configuration(instance_name)
        self.repo, self.cnx = in_memory_repo_cnx(
            config, login=login, password=password)
        self.session = self.repo._get_session(self.cnx.sessionid)

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def insert(self, wave_name, wave_category, wave_dict,
               wave_description, extra_answers=None):
        """ Insert a new wave of snaps.

        Parameters
        ----------
        wave_name: str
            the name of the current wave.
        wave_category: str
            a category used to filter waves.
        wave_dict: dict
            a dictionary structure of the form:
            {subject_id: {snaps: {filepaths: [filepath list],
                                  dtype: description of the tool to use}}
        wave_description: str
            the description of the wave formated in RST.
        extra_answers: list of str (optional, default=None)
            a list of closed possible extra answers.
        """

        # Format the 'extra_answers' parameter if necessary
        extra_answers = extra_answers or []

        # Transform the RST documentation in HTML
        wave_description = rst2html(wave_description)

        # Insert the wave entity if necessary
        print("Inserting wave '{0}'...".format(wave_name))
        wave_struct = {
            "identifier": self._md5_sum(wave_name),
            "name": wave_name.replace("_", " "),
            "category": wave_category.replace("_", " "),
            "description": wave_description,
            "extra_answers": json.dumps(extra_answers)
        }
        wave_entity, wave_created = self._get_or_create_unique_entity(
            rql=("Any X Where X is Wave, X identifier "
                 "'{0}'".format(wave_struct["identifier"])),
            check_unicity=True,
            entity_name="Wave",
            **self._u(wave_struct))
        wave_eid = wave_entity.eid

        # Insert the snaps if necassary
        cnt = 0
        tot = len(wave_dict.keys())
        print("Inserting '{0}' snapsets...".format(
            len(wave_dict.keys())))
        for subject, snaps in wave_dict.items():
            cnt += 1
                # > display progress
            ratio = float(cnt + 1) / tot
            self._progress_bar(ratio, title="SNAPS", bar_length=40)

            snapSet_struct = {
                "identifier": self._md5_sum("{}{}".format(
                    wave_name, subject)),
                "name": "{}_{}".format(wave_name.replace("_", " "),
                                       subject)
                }
            snapSet_entity, snapSet_created = \
                self._get_or_create_unique_entity(
                    rql=("Any X Where X is SnapSet, X identifier "
                         "'{0}'".format(
                             snapSet_struct["identifier"])),
                    check_unicity=True,
                    entity_name="SnapSet",
                    **self._u(snapSet_struct))
            snapSet_eid = snapSet_entity.eid

            for snap_key, snap_val in snaps.items():
                # > create entity
                snap_struct = {
                    "identifier": self._md5_sum("{}{}{}".format(wave_name,
                                                                subject,
                                                                snap_key)),
                    "name": snap_key,
                    "absolute": True,
                    "filepaths": Binary(json.dumps(snap_val["filepaths"])),
                    "dtype": snap_val["dtype"]
                }
                snap_entity, snap_created = self._get_or_create_unique_entity(
                    rql=("Any X Where X is Snap, X identifier "
                         "'{0}'".format(snap_struct["identifier"])),
                    check_unicity=True,
                    entity_name="Snap",
                    **self._u(snap_struct))
                snap_eid = snap_entity.eid

                if snap_created:
                    self._set_unique_relation(
                        snap_eid, "snapset", snapSet_eid,
                        check_unicity=False)
                    self._set_unique_relation(
                        snapSet_eid, "snaps", snap_eid,
                        check_unicity=False)

            # add relations
            if snapSet_created:
                self._set_unique_relation(
                    snapSet_eid, "wave", wave_eid,
                    check_unicity=False)
                self._set_unique_relation(
                    wave_eid, "snapsets", snapSet_eid,
                    check_unicity=False)

        self.session.commit()

    def add_user(self, user_name, password, group_name="users"):
        """ Add a new user in the database.

        Parameters
        ----------
        user_name: str
            the login of the user in the database.
        password: str
            the password of the user in the database.
        group_name: str
            the database group name the user will be rattached to.
        """
        # Get the activated State entity
        rql = "Any X Where X is State, X name 'activated'"
        rset = self.session.execute(rql)
        if rset.rowcount != 1:
            raise Exception("Can't insert users, no activated State entity "
                            "detected.")
        state_eid = rset[0][0]

        # Insert the user
        crypted = crypt_password(password)
        user_entity, is_created = self._get_or_create_unique_entity(
            rql=("Any X Where X is CWUser, X login "
                 "'{0}'".format(user_name)),
            check_unicity=True,
            entity_name="CWUser",
            login=unicode(user_name),
            upassword=Binary(crypted))

        # If the user is created, add relation with the State entity
        if is_created:

            # Activate the account
            self._set_unique_relation(
                user_entity.eid, "in_state", state_eid, check_unicity=False)

            # Add the user to the default group
            rset = self.session.execute(
                "Any X Where X is CWGroup, X name '{0}'".format(group_name))
            if rset.rowcount != 1:
                raise Exception(
                    "Can't insert user '{0}' in group '{1}', got {2} "
                    "matches.".format(user_name, group_name, rset.rowcount))
            group_eid = rset[0][0]
            self._set_unique_relation(
                user_entity.eid, "in_group", group_eid, check_unicity=False)

    ###########################################################################
    #   Private Methods
    ###########################################################################

    def _md5_sum(self, path, algo="md5"):
        """ Create a md5 sum of a path.

        Parameters
        ----------
        path: str (madatory)
            a string to hash.

        Returns
        -------
        out: str
            the input hashed string.
        """
        if hasattr(hashlib, algo):
            m = getattr(hashlib, algo)()
        else:
            m = hashlib.md5()
        m.update(path)
        return m.hexdigest()

    def _progress_bar(self, ratio, title="", bar_length=40):
        """ Method to generate a progress bar.

        Parameters
        ----------
        ratio: float (mandatory 0<ratio<1)
            float describing the current processing status.
        title: str (optional)
            a title to identify the progress bar.
        bar_length: int (optional)
            the length of the bar that will be ploted.
        """
        progress = int(ratio * 100.)
        block = int(round(bar_length * ratio))
        text = "\r{2} in Progress: [{0}] {1}%".format(
            "=" * block + " " * (bar_length - block), progress, title)
        sys.stdout.write(text)
        if ratio == 1:
            sys.stdout.write("\n")

    def _u(self, struct):
        """ Transform string to unicode

        Parameters
        ----------
        struct: dict
            a simple one level dictionary.
        """
        for key, value in struct.items():
            if isinstance(value, str):
                struct[key] = unicode(value)
        return struct

    ###########################################################################
    #   Private Insertion Methods
    ###########################################################################

    def _set_unique_relation(self, source_eid, relation_name, detination_eid,
                             check_unicity=True, subjtype=None):
        """ Method to create a new unique relation.

        First check that the relation do not exists if 'check_unicity' is True.

        Parameters
        ----------
        source_eid: int (madatory)
            the CW identifier of the object entity in the relation.
        relation_name: str (madatory)
            the relation name.
        detination_eid: int (madatory)
            the CW identifier of the subject entity in the relation.
        check_unicity: bool (optional)
            if True check if the relation already exists in the data base.
        subjtype: str (optional)
            give the subject etype for inlined relation when using a store.
        """
        # With unicity contrain
        if check_unicity:

            # First build the rql request
            rql = "Any X Where X eid '{0}', X {1} Y, Y eid '{2}'".format(
                source_eid, relation_name, detination_eid)

            # Execute the rql request
            rset = self.session.execute(rql)

            # The request returns some data -> do nothing
            if rset.rowcount == 0:
                self.session.add_relation(
                    source_eid, relation_name, detination_eid)

        # Without unicity constrain
        else:
            self.session.add_relation(
                source_eid, relation_name, detination_eid)

    def _get_or_create_unique_entity(self, rql, entity_name,
                                     check_unicity=True, *args, **kwargs):
        """ Method to create a new unique entity.

        First check that the entity do not exists by executing the rql request
        if 'check_unicity' is True.

        Parameters
        ----------
        rql: str (madatory)
            the rql request to check unicity.
        entity_name: str (madatory)
            the name of the entity we want to create.
        check_unicity: bool (optional)
            if True check if the entity already exists in the data base.

        Returns
        -------
        entity: CW entity
            the requested entity.
        is_created: bool
            return True if the entity has been created, False otherwise.
        """
        # Initilize output prameter
        is_created = False

        # With unicity contrain
        if check_unicity:
            # First execute the rql request
            rset = self.session.execute(rql)

            # The request returns some data, get the unique entity
            if rset.rowcount > 0:
                if rset.rowcount > 1:
                    raise Exception("The database is corrupted, please "
                                    "investigate.")
                entity = rset.get_entity(0, 0)
            # Create a new unique entity
            else:
                entity = self.session.create_entity(entity_name, **kwargs)
                is_created = True
        # Without unicity constrain
        else:
            entity = self.session.create_entity(entity_name, **kwargs)
            is_created = True

        return entity, is_created
