"""Tools for working with Dimensions."""
from typing import Optional, Type, List
from uuid import uuid4, UUID

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.descriptors import Descriptor, RealDescriptor

__all__ = ['Dimension', 'ContinuousDimension', 'EnumeratedDimension']


class Dimension(PolymorphicSerializable['Dimension']):
    """A Citrine Dimension - an abstract type that returns the proper
    subtype based on the 'type' value of the passed in dict.
    """

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            'ContinuousDimension': ContinuousDimension,
            'EnumeratedDimension': EnumeratedDimension
        }[data['type']]


class ContinuousDimension(Serializable['ContinuousDimension'], Dimension):
    """Continuous dimension that is defined by a template ID, material descriptor, lower bound, and upper bound.

    Parameters
    ----------
    descriptor: RealDescriptor
        a descriptor of the single dimension
    lower_bound: float
        inclusive lower bound
    upper_bound: float
        inclusive upper bound
    template_id: UUID
        UUID that corresponds to the template in DC
    """

    descriptor = properties.Object(RealDescriptor, 'descriptor')
    lower_bound = properties.Float('lower_bound')
    upper_bound = properties.Float('upper_bound')
    typ = properties.String('type', default='ContinuousDimension', deserializable=False)
    template_id = properties.UUID('template_id', default=uuid4())

    def __init__(self,
                 descriptor: RealDescriptor,
                 lower_bound: Optional[float] = None,
                 upper_bound: Optional[float] = None,
                 template_id: Optional[UUID] = None):
        self.descriptor: RealDescriptor = descriptor
        self.lower_bound: float = lower_bound or descriptor.lower_bound
        self.upper_bound: float = upper_bound or descriptor.upper_bound
        self.template_id: UUID = template_id or uuid4()


class EnumeratedDimension(Serializable['EnumeratedDimension'], Dimension):
    """Finite enumerated dimension that is defined by a template ID, material descriptor, and a list of values
    for that descriptor.

    Parameters
    ----------
    descriptor: Descriptor
        a descriptor of the single dimension
    template_id: UUID
        UUID that corresponds to the template in DC
    values: list[str]
        list of values that can be parsed by the descriptor
    """

    descriptor = properties.Object(Descriptor, 'descriptor')
    values = properties.List(properties.String(), 'list')
    typ = properties.String('type', default='EnumeratedDimension', deserializable=False)
    template_id = properties.UUID('template_id', default=uuid4())

    def __init__(self,
                 descriptor: Descriptor,
                 values: List[str],
                 template_id: Optional[UUID] = None):
        self.descriptor: Descriptor = descriptor
        self.values: List[str] = values
        self.template_id: UUID = template_id or uuid4()
