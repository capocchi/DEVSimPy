from ApplicationController import TestApp
    
# Exemple de code PlantUML pour le component diagram
puml_component = """@startuml
!theme plain
skinparam linetype polyline

package "TestModel" {

  component "Generator" as Generator {
    portout out0
  }

  component "Processor" as Processor {
    portin in0
    portout out0
  }

  package "Coupled_System" as Coupled_System {

    component "SubProcessor1" as SubProcessor1 {
      portin in0
      portout out0
    }

    component "SubProcessor2" as SubProcessor2 {
      portin in0
      portout out0
    }

    ' Connections
    SubProcessor1 --> SubProcessor2 : out0→in0

  }

  component "Collector" as Collector {
    portin in0
  }

  ' Connections
  Generator --> Processor : out0→in0
  Processor --> Coupled_System : out0→in0
  Coupled_System --> Collector : out0→in0

}

@enduml"""

# Exemple de code PlantUML pour le class diagram
puml_class = """@startuml
!theme plain
skinparam classAttributeIconSize 0
skinparam class {
  BackgroundColor<<atomic>> LightBlue
  BackgroundColor<<coupled>> LightGreen
  BackgroundColor<<framework>> WhiteSmoke
}

package "DEVS Framework" {

  abstract class DomainBehavior <<framework>> {
    ' DomainInterface.DomainBehavior
    # state : dict
    --
    + intTransition()
    + extTransition(inputs)
    + outputFnc()
    + timeAdvance()
  }

  abstract class DomainStructure <<framework>> {
    ' DomainInterface.DomainStructure
    # IPorts : list
    # OPorts : list
    # componentSet : dict
    --
    + addInPort(name)
    + addOutPort(name)
    + addSubModel(model)
  }

  class Coupled <<framework>> {
    ' DomainInterface.Coupled
    # IC : list
    # EIC : list
    # EOC : list
    --
    + select(models)
  }

}

package "User Models" {

  class Generator <<atomic>> {
    ' MyLibrary.Generator
    - period : float
    - count : int
    --
    + out0 : OutputPort
    --
    + intTransition()
    + outputFnc()
    + timeAdvance()
  }

  class Processor <<atomic>> {
    ' MyLibrary.Processor
    - processing_time : float
    --
    + in0 : InputPort
    + out0 : OutputPort
    --
    + extTransition(inputs)
    + outputFnc()
  }

  class Collector <<atomic>> {
    ' MyLibrary.Collector
    - data : list
    --
    + in0 : InputPort
    --
    + extTransition(inputs)
  }

  class CoupledSystem <<coupled>> {
    ' MyLibrary.CoupledSystem
  }

}

' Inheritance relationships
DomainBehavior <|-- Generator
DomainBehavior <|-- Processor
DomainBehavior <|-- Collector
DomainStructure <|-- Coupled
Coupled <|-- CoupledSystem

@enduml"""

    # Informations du diagramme
diagram_info = """Path: /home/user/models/TestModel.dsp
Number of atomic devs models: 5
Number of coupled devs models: 1
Number of coupling: 4
Number of deep level (description hierarchy): 2
Number of input port models: 0
Number of output port models: 0"""

import wx

from ApplicationController import TestApp
from DiagramInfoDialog import DiagramInfoDialog

# Run the test
app = TestApp(0)

dlg = DiagramInfoDialog(None, diagram_info, puml_component, puml_class)

app.RunTest(dlg)
