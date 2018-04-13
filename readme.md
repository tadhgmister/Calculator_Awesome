# Calculator readme



## Sections

### Core
This module will take an Abstract Syntax Tree (AST) and delegate it to other modules. (rendering and evaluating)

### Lexar and Parser
This module will take a string of user input and parse it into a AST like structure which can be used by the core.  

One implementation will be to use python's built in AST module to parse expressions but this heavily limits the notations that are considered legal.

Ideally extensions may have syntax or symbols that it can implement such as error propogation adding a +- operator, or matrix/vector adding lists.  Using the python AST makes what operations can be implemented is very limited so developing a full parser will need to be done eventually.

### Environment
this module is responsible for keeping track of which module implementations are being used, which extensions are currently in use, manipulating persistant data. 

One implementation which will likely be used to test the other modules is to use Jupyter Notebook to keep track of everything, it has persistant data in notebooks with variables, statements, and has access to python code between steps which can be used for testing.

### Interface
The interface which users interact with to use the calculator.  Initially Jupyter notebook will be used but a stand alone HTML interface is desired.

### Rendering
Rendering involves converting the AST into rendered equations with variable substitutions and final answers.  This will likely be absorbed into specific extensions to render themselves, however some standard regarding rendering formats needs to be established.  

Initially I would like everything to be exportable as Latex code and possibly MathML for the HTML interface, more work on this module will be needed if the calculator is to be exported to hardware.