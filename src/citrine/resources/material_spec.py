"""Resources that represent material spec data objects."""
from typing import List, Dict, Optional, Type

from citrine._utils.functions import set_default_uid
from citrine._rest.resource import Resource
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine._serialization.properties import String, LinkOrElse, Mapping, Object
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine.attributes.property_and_conditions import PropertyAndConditions
from taurus.entity.file_link import FileLink
from taurus.entity.object.material_spec import MaterialSpec as TaurusMaterialSpec
from taurus.entity.object.process_spec import ProcessSpec as TaurusProcessSpec
from taurus.entity.template.material_template import MaterialTemplate as TaurusMaterialTemplate


class MaterialSpec(DataConcepts, Resource['MaterialSpec'], TaurusMaterialSpec):
    """
    A material specification.

    Parameters
    ----------
    name: str
        Name of the material spec.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/taurus-documentation/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/taurus-documentation/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    notes: str, optional
        Long-form notes about the material spec.
    process: ProcessSpec
        Process that produces this material.
    properties: List[PropertyAndConditions], optional
        Properties of the material, along with an optional list of conditions under which
        those properties are measured.
    template: MaterialTemplate, optional
        A template bounding the valid values for this material's properties.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.

    """

    _response_key = TaurusMaterialSpec.typ  # 'material_spec'

    name = String('name')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    notes = PropertyOptional(String(), 'notes')
    process = PropertyOptional(LinkOrElse(), 'process')
    properties = PropertyOptional(PropertyList(Object(PropertyAndConditions)), 'properties')
    template = PropertyOptional(LinkOrElse(), 'template')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 process: Optional[TaurusProcessSpec] = None,
                 properties: Optional[List[PropertyAndConditions]] = None,
                 template: Optional[TaurusMaterialTemplate] = None,
                 file_links: Optional[List[FileLink]] = None):
        DataConcepts.__init__(self, TaurusMaterialSpec.typ)
        TaurusMaterialSpec.__init__(self, name=name, uids=set_default_uid(uids),
                                    tags=tags, process=process, properties=properties,
                                    template=template, file_links=file_links, notes=notes)

    def __str__(self):
        return '<Material spec {!r}>'.format(self.name)


class MaterialSpecCollection(DataConceptsCollection[MaterialSpec]):
    """Represents the collection of all material specs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/material-specs'
    _dataset_agnostic_path_template = 'projects/{project_id}/material-specs'
    _individual_key = 'material_spec'
    _collection_key = 'material_specs'

    @classmethod
    def get_type(cls) -> Type[MaterialSpec]:
        """Return the resource type in the collection."""
        return MaterialSpec
