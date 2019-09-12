"""Resources that represent ingredient spec data objects."""
from typing import List, Dict, Optional, Type

from citrine._utils.functions import set_default_uid
from citrine._rest.resource import Resource
from citrine.resources.data_concepts import DataConceptsCollection, DataConcepts
from citrine.resources.material_spec import MaterialSpec
from citrine._serialization.properties import Mapping, String, LinkOrElse, Object
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from taurus.entity.file_link import FileLink
from taurus.entity.object.ingredient_spec import IngredientSpec as TaurusIngredientSpec
from taurus.entity.value.continuous_value import ContinuousValue


class IngredientSpec(DataConcepts, Resource['IngredientSpec'], TaurusIngredientSpec):
    """
    An ingredient specification.

    Ingredients annotate a material with information about its usage in a process.

    Parameters
    ----------
    uids: Map[str, str], optional
        A collection of unique identifiers, each a key-value pair. The key is the "scope"
        and the value is the identifier. The scope "id" is reserved for the internal Citrine ID,
        which will always be a uuid4.
    tags: List[str], optional
        A set of tags. Tags can be used for filtering.
    notes: str, optional
        Long-form notes about the ingredient spec.
    material: MaterialSpec
        Material that this ingredient is.
    mass_fraction: :py:class:`ContinuousValue \
    <taurus.entity.value.continuous_value.ContinuousValue>`, optional
        The mass fraction of the ingredient in the process.
    volume_fraction: :py:class:`ContinuousValue \
    <taurus.entity.value.continuous_value.ContinuousValue>`, optional
        The volume fraction of the ingredient in the process.
    number_fraction: :py:class:`ContinuousValue \
    <taurus.entity.value.continuous_value.ContinuousValue>`, optional
        The number fraction of the ingredient in the process.
    absolute_quantity: :py:class:`ContinuousValue \
    <taurus.entity.value.continuous_value.ContinuousValue>`, optional
        The absolute quantity of the ingredient in the process.
    name: str, optional
        Label on the ingredient that is unique within the process that contains it.
    labels: List[str], optional
        Additional labels on the ingredient that must be unique.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.

    """

    _response_key = TaurusIngredientSpec.typ  # 'ingredient_spec'

    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    notes = PropertyOptional(String(), 'notes')
    material = PropertyOptional(LinkOrElse(), 'material')
    mass_fraction = PropertyOptional(Object(ContinuousValue), 'mass_fraction')
    volume_fraction = PropertyOptional(Object(ContinuousValue), 'volume_fraction')
    number_fraction = PropertyOptional(Object(ContinuousValue), 'number_fraction')
    absolute_quantity = PropertyOptional(
        Object(ContinuousValue), 'absolute_quantity')
    name = PropertyOptional(String(), 'name')
    labels = PropertyOptional(PropertyList(String()), 'labels')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    typ = String('type')

    def __init__(self,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 material: Optional[MaterialSpec] = None,
                 mass_fraction: Optional[ContinuousValue] = None,
                 volume_fraction: Optional[ContinuousValue] = None,
                 number_fraction: Optional[ContinuousValue] = None,
                 absolute_quantity: Optional[ContinuousValue] = None,
                 name: Optional[str] = None,
                 labels: Optional[List[str]] = None,
                 file_links: Optional[List[FileLink]] = None):
        DataConcepts.__init__(self, TaurusIngredientSpec.typ)
        TaurusIngredientSpec.__init__(self, uids=set_default_uid(uids), tags=tags, notes=notes,
                                      material=material, mass_fraction=mass_fraction,
                                      volume_fraction=volume_fraction,
                                      number_fraction=number_fraction,
                                      absolute_quantity=absolute_quantity, labels=labels,
                                      name=name, file_links=file_links)

    def __str__(self):
        return '<Ingredient spec {!r}>'.format(self.name)


class IngredientSpecCollection(DataConceptsCollection[IngredientSpec]):
    """Represents the collection of all ingredient specs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/ingredient-specs'
    _dataset_agnostic_path_template = 'projects/{project_id}/ingredient-specs'
    _individual_key = 'ingredient_spec'
    _collection_key = 'ingredient_specs'

    @classmethod
    def get_type(cls) -> Type[IngredientSpec]:
        """Return the resource type in the collection."""
        return IngredientSpec
