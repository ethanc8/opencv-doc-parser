import cv2
from enum import Enum
import inspect
from typing import Callable
import typeshed_client
import ast

class ParamData:
    def __init__(self):
        self.name: str = ""
        self.brief: str = ""
        self.type: str = ""

    def __repr__(self):
        return str(self.__dict__)

class NoteData:
    def __init__(self):
        self.type: str = ""
        self.note: str = ""


class FunctionData:
    def __init__(self):
        self.function: Callable = None
        self.name: str = ""
        self.brief: str = ""
        self.docstringSignature: str = ""
        self.params: dict[str, ParamData] = dict()
        self.notes: list[str] = []
        self.description: str = ""
        self.returnDescription: str = ""
        self.returnType: str = "object"

    def __repr__(self):
        return str(self.__dict__)
        # return str(self.params)

class Reference:
    def setValue(self, value): pass
    def getValue(self): pass

class AttributeReference:
    target: object
    attrname: tuple | str
    def __init__(self, target, attrname):
        self.target = target
        self.attrname = attrname
    def getValue(self):
        return getattr(self.target, self.attrname)
    def setValue(self, value):
        setattr(self.target, self.attrname, value)

class IndexReference:
    target: object
    index: object
    def __init__(self, target, index):
        self.target = target
        self.index = index
    def getValue(self):
        return self.target[self.index]
    def setValue(self, value):
        self.target[self.index] = value

def parseDocstringOf(function: Callable, data: FunctionData):
    retval = ""
    lines = function.__doc__.splitlines()
    data.docstringSignature = lines.pop(0)
    curData: Reference = None
    for line in lines:
        line = line.lstrip(" .*")
        line = line.strip()
        line = line.replace("\\f$", "$")
        # print(line)
        if line.startswith("@brief "):
            data.brief = line.removeprefix("@brief ")
            curData = AttributeReference(data, "brief")
        elif line.startswith("@param "):
            splitline = line.split()
            paramName = splitline[1]
            if paramName not in data.params:
                data.params[paramName] = ParamData()
            param = data.params[paramName]
            param.name = splitline[1]
            param.brief = " ".join(splitline[2:])
            curData = AttributeReference(param, "brief")
            # data.params.append(param)
        elif line.startswith("@return "):
            data.returnDescription = line.removeprefix("@return ")
            curData = AttributeReference(param, "returnDescription")
        elif line.startswith("@note "):
            note = NoteData()
            note.type = "note"
            note.note = line.removeprefix("@note ")
            data.notes.append(note)
            curData = AttributeReference(note, "note")
        elif line.startswith("@sa "):
            note = NoteData()
            note.type = "sa"
            note.note = line.removeprefix("@sa ")
            data.notes.append(note)
            curData = AttributeReference(note, "note")
        elif line.startswith("@deprecated "):
            note = NoteData()
            note.type = "deprecated"
            note.note = line.removeprefix("@deprecated ")
            data.notes.append(note)
            curData = AttributeReference(note, "note")
        elif line == "":
            curData = None
        else:
            if curData is None:
                curData = AttributeReference(data, "description")
            curData.setValue(curData.getValue() + line + " ")
    # return data

def documentFunction(name) -> str:
    # print(f"Documenting {name}...")
    function = eval(name)
    data = FunctionData()
    parseDocstringOf(function, data)
    parseAstOf(name, data)
    retval = ""
    retval += "````{py:function} "
    retval += data.docstringSignature
    retval += "\n\n"
    retval += data.brief
    retval += "\n\n"
    retval += data.description
    for note in data.notes:
        if note.type == "note":
            retval += f"\n```{{note}}\n{note.note}\n```"
        elif note.type == "sa":
            retval += f"\n**See also:** {note.note}"
        elif note.type == "deprecated":
            retval += f"\n```{{deprecated}} unknown\n{note.note}\n```"
            # retval += f"\n**Deprecated:** {note.note}"
    retval += "\n\n"
    for param in data.params.values():
        # retval += f"\n:param {param.type} {param.name}: {param.brief}"
        retval += f"\n:param {param.name}: {param.brief}\n:type {param.name}: {param.type}"
    if data.returnDescription != "":
        retval += f"\n:return: {data.returnDescription}"
    if data.returnType != "":
        retval += f"\n:rettype: {data.returnType}"
    retval += "\n````"
    return retval

def documentFunctionsInModule(moduleName) -> str:
    module = eval(moduleName)
    functions: list[Callable] = inspect.getmembers(module, lambda x: callable(x) and not inspect.isclass(x))
    # print(functions)
    retval = "## Functions\n"
    for name, function in functions:
        retval += documentFunction(moduleName + "." + name)
        retval += "\n\n\n"
    return retval

def documentModule(moduleName) -> str:
    retval = f"# `{moduleName}`\n"
    retval += f"```{{py:module}} {moduleName}\n{eval(moduleName).__doc__}\n```\n"
    retval += documentFunctionsInModule(moduleName) + "\n"
    return retval

def astOfFunction(name) -> ast.FunctionDef:
    resolver = typeshed_client.Resolver()
    nameInfo = resolver.get_fully_qualified_name(name)
    if nameInfo is None:
        return None
    if isinstance(nameInfo.ast, typeshed_client.OverloadedName):
        return nameInfo.ast.definitions[0]
    return nameInfo.ast

def parseAstOf(name: str, data: FunctionData):
    functionAST = astOfFunction(name)
    if functionAST is None:
        return
    for arg in functionAST.args.args:
        paramName = arg.arg
        if paramName not in data.params:
            data.params[paramName] = ParamData()
        param = data.params[paramName]
        param.name = paramName
        param.type = ast.unparse(ast.fix_missing_locations(arg.annotation))
    data.returnType = ast.unparse(ast.fix_missing_locations(functionAST.returns))

# print(documentFunction(cv2.aruco.calibrateCameraCharucoExtended))
# print(documentFunction("cv2.aruco.calibrateCameraCharucoExtended"))
print(documentModule("cv2.aruco"))
# print(astOfFunction("cv2.aruco.calibrateCameraCharucoExtended"))
