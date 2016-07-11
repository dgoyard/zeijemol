# -*- coding: utf-8 -*-
# copyright 2016 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr -- mailto:contact@logilab.fr
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from yams.buildobjs import EntityType
from yams.buildobjs import String
from yams.buildobjs import Boolean
from yams.buildobjs import Bytes
from yams.buildobjs import SubjectRelation
from cubicweb.schema import ERQLExpression


###############################################################################
# Modification of the schema
###############################################################################

class Snap(EntityType):
    """ An entity used to store the path to a snap file on the central
    repository.

    Attributes
    ----------
    identifier: String (mandatory)
        a unique identifier for the entity.
    name: String (mandatory)
        a short description of the file.
    absolute: Boolean (optional)
        tells us if the path stored is absolute.
    filepath: String (mandatory)
        the snap file path.
    dtype: String (mandatory)
        the file type: only 'PNG' or 'JPEG' are supported.
    data_sha1hex: String (optional)
        the SHA1 sum of the file.
    code: String (optional)
        a code associated to the snap

    Relations
    ---------
    wave: SubjectRelation
        a snap is connected to one wave.
    scores: SubjectRelation
        a score is connected to one snap.
    """
    identifier = String(
        required=True,
        unique=True,
        maxsize=64,
        description=u"a unique identifier for the entity.")
    name = String(
        required=True,
        fulltextindexed=True,
        maxsize=256,
        description=u"a short description of the file.")
    absolute = Boolean(
        default=True,
        description=u"tells us if the path stored is absolute.")
    filepaths = Bytes(
        required=True,
        fulltextindexed=True,
        description=u"the snap file paths.")
    dtype = String(
        required=True,
        indexed=True,
        vocabulary=("CTM", "IM", "triplanar"),
        description=u"the tools type: 'CTM', 'IM', 'triplanar'")
    snapset = SubjectRelation(
        "SnapSet",
        cardinality="1*",
        inlined=False)


class Wave(EntityType):
    """ An entity used to store QC wave inforamtion.

    Attributes
    ----------
    identifier: String (mandatory)
        a unique identifier for the entity.
    name: String (mandatory)
        a short description of the wave.
    category: String (mandatory)
        a category used to filter waves.
    description: String (mandatory)
        a long description of the wave.
    extra_answers: String
        a list of closed possible extra answers.

    Relations
    ---------
    snaps: SubjectRelation
        a snap is connected to one wave.
    """
    identifier = String(
        required=True,
        unique=True,
        maxsize=64,
        description=u"a unique identifier for the entity.")
    name = String(
        required=True,
        fulltextindexed=True,
        maxsize=256,
        description=u"a short description of the wave.")
    category = String(
        required=True,
        indexed=True,
        maxsize=64,
        description=u"a category used to filter waves.")
    description = String(
        required=True,
        description=u"a long description of the wave.")
    extra_answers = String(
        description=u"a list of closed possible extra answers.")
    snapsets = SubjectRelation(
        "SnapSet",
        cardinality="*1",
        inlined=False)


class SnapSet(EntityType):
    """ An entity used to group within each wave, the snaps related to one
        subject.

    Attributes
    ----------
    identifier: String (mandatory)
        a unique identifier for the entity.
    name: String (mandatory)
        a short description of the wave.

    Relations
    ---------
    snaps: SubjectRelation
        a SnapSet is connected to one wave.
    """
    identifier = String(
        required=True,
        unique=True,
        maxsize=64,
        description=u"a unique identifier for the entity.")
    name = String(
        required=True,
        fulltextindexed=True,
        maxsize=256,
        description=u"Snapset name")
    snaps = SubjectRelation(
        "Snap",
        cardinality="*1",
        inlined=False)
    wave = SubjectRelation(
        "Wave",
        cardinality="1*",
        inlined=False)
    scores = SubjectRelation(
        "Score",
        cardinality="*1",
        inlined=False)


class Score(EntityType):
    """ An entity used to store the rate associated to a snap file.

    Attributes
    ----------
    identifier: String (mandatory)
        a unique identifier for the entity.
    uid: String (mandatory)
        the user that have scored the snap file.
    score: String (mandatory)
        the user score.

    Relations
    ---------
    snap: SubjectRelation
        a score is connected to one snap.
    scored_by: SubjectRelation
        a score is realted to one user of the database.
    """
    identifier = String(
        required=True,
        unique=True,
        maxsize=64,
        description=u"a unique identifier for the entity.")
    uid = String(
        required=True,
        fulltextindexed=True,
        maxsize=64,
        description=u"the user that have scored the snap file")
    score = String(
        required=True,
#        vocabulary=("Accept", "Exclude"),
        description=u"the user score.")
    extra_scores = String(
        description=u"the extra user scores.")
    snapset = SubjectRelation(
        "SnapSet",
        cardinality="1*",
        inlined=False)
    # composite object: if CWUser is deleted, the scores are deleted too
    scored_by = SubjectRelation(
        "CWUser",
        cardinality="1*",
        inlined=False,
        composite="object")


###############################################################################
# Set permissions
###############################################################################

SCORE_PERMISSIONS = {
    "read": (
        "managers",
        ERQLExpression("X scored_by U")),
    "add": ("managers", "users"),
    "update": ("managers", ),
    "delete": ("managers", ),
}
Score.set_permissions(SCORE_PERMISSIONS)
