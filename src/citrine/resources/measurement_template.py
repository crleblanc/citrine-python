"""Resources that represent measurement templates."""
from typing import List, Dict, Optional, Union, Sequence, Type

from citrine._rest.resource import Resource
from citrine._session import Session
from citrine._serialization.properties import String, Mapping, Object, MixedList, LinkOrElse
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._utils.functions import set_default_uid
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine.resources.property_template import PropertyTemplate
from citrine.resources.parameter_template import ParameterTemplate
from citrine.resources.condition_template import ConditionTemplate
from taurus.client.json_encoder import loads, dumps
from taurus.entity.template.measurement_template \
    import MeasurementTemplate as TaurusMeasurementTemplate
from taurus.entity.bounds.base_bounds import BaseBounds
from taurus.entity.link_by_uid import LinkByUID


class MeasurementTemplate(DataConcepts, Resource['MeasurementTemplate'],
                          TaurusMeasurementTemplate):
    """
    A measurement template.

    Measurement templates are collections of condition, parameter and property templates that
    constrain the values of a measurement's condition, parameter and property attributes, and
    provide a common structure for describing similar measurements.

    Parameters
    ----------
    name: str
        The name of the measurement template.
    description: str, optional
        Long-form description of the measurement template.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/taurus-documentation/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/taurus-documentation/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    conditions: List[ConditionTemplate] or List[ConditionTemplate, \
    :py:class:`BaseBounds <taurus.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated conditions. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this condition.
    parameters: List[ParameterTemplate] or List[ParameterTemplate, \
    :py:class:`BaseBounds <taurus.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated parameters. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this parameter.
    properties: List[PropertyTemplate] or List[PropertyTemplate, \
    :py:class:`BaseBounds <taurus.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated properties. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this property.

    """

    _response_key = TaurusMeasurementTemplate.typ  # 'measurement_template'

    name = String('name')
    description = PropertyOptional(String(), 'description')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    properties = PropertyOptional(PropertyList(
        MixedList([LinkOrElse, Object(BaseBounds)])), 'properties')
    conditions = PropertyOptional(PropertyList(
        MixedList([LinkOrElse, Object(BaseBounds)])), 'conditions')
    parameters = PropertyOptional(PropertyList(
        MixedList([LinkOrElse, Object(BaseBounds)])), 'parameters')
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 properties: Optional[Sequence[Union[PropertyTemplate,
                                                     LinkByUID,
                                                     Sequence[Union[PropertyTemplate, LinkByUID,
                                                                    BaseBounds]]
                                                     ]]] = None,
                 conditions: Optional[Sequence[Union[ConditionTemplate,
                                                     LinkByUID,
                                                     Sequence[Union[ConditionTemplate, LinkByUID,
                                                                    BaseBounds]]
                                                     ]]] = None,
                 parameters: Optional[Sequence[Union[ParameterTemplate,
                                                     LinkByUID,
                                                     Sequence[Union[ParameterTemplate, LinkByUID,
                                                                    BaseBounds]]
                                                     ]]] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        DataConcepts.__init__(self, TaurusMeasurementTemplate.typ)
        TaurusMeasurementTemplate.__init__(self, name=name, properties=properties,
                                           conditions=conditions, parameters=parameters, tags=tags,
                                           uids=set_default_uid(uids), description=description)

    @classmethod
    def _build_child_objects(cls, data: dict, session: Session = None):
        """
        Build the condition, parameter, and property templates and bounds.

        Parameters
        ----------
        data: dict
            A serialized material template.
        session: Session, optional
            Citrine session used to connect to the database.

        Returns
        -------
        None
            The serialized measurement template is modified so that its conditions are now a list
            of object pairs of the form [ConditionTemplate, Bounds], the parameters are
            [ParameterTemplate, Bounds], and the properties are [PropertyTemplate, Bounds].

        """
        if 'properties' in data and len(data['properties']) != 0:
            data['properties'] = [[PropertyTemplate.build(prop[0].as_dict()),
                                   loads(dumps(prop[1]))] for prop in data['properties']]
        if 'conditions' in data and len(data['conditions']) != 0:
            data['conditions'] = [[ConditionTemplate.build(cond[0].as_dict()),
                                   loads(dumps(cond[1]))] for cond in data['conditions']]
        if 'parameters' in data and len(data['parameters']) != 0:
            data['parameters'] = [[ParameterTemplate.build(param[0].as_dict()),
                                   loads(dumps(param[1]))] for param in data['parameters']]

    def __str__(self):
        return '<Measurement template {!r}>'.format(self.name)


class MeasurementTemplateCollection(DataConceptsCollection[MeasurementTemplate]):
    """A collection of measurement templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/measurement-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/measurement-templates'
    _individual_key = 'measurement_template'
    _collection_key = 'measurement_templates'

    @classmethod
    def get_type(cls) -> Type[MeasurementTemplate]:
        """Return the resource type in the collection."""
        return MeasurementTemplate
