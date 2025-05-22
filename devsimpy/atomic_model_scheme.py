from typing import Literal
from pydantic import BaseModel


class State(BaseModel):
    name: str
    time: str | int | float


class ModelProperty(BaseModel):
    name: str
    var_type: str
    value: str | float | int
    description: str


class Function(BaseModel):
    description: str
    parameters: str


class Specifications(BaseModel):
    input_port: int
    output_port: int
    model_name: str
    model_type: Literal["Generator", "Collector", "Default"]
    states: list[State]
    model_description: str
    initial_state: State
    model_properties: list[ModelProperty]


class AtomicModel(BaseModel):
    specifications: Specifications
    init_function: Function
    ext_transition: Function
    int_transition: Function
    output_function: Function
    time_advance: Function
