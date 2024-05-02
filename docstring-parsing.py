import cv2
from enum import Enum
import inspect
from typing import Callable

class ParamData:
    def __init__(self):
        self.name: str = ""
        self.brief: str = ""
        self.type: object = None

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
        self.params: list[ParamData] = []
        self.notes: list[str] = []
        self.description: str = ""
        self.returnDescription: str = ""
        self.returnType: object = None

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

def parseDocstringOf(function: Callable) -> FunctionData:
    retval = ""
    data = FunctionData()
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
            param = ParamData()
            splitline = line.split()
            param.name = splitline[1]
            param.brief = " ".join(splitline[2:])
            curData = AttributeReference(param, "brief")
            data.params.append(param)
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
    return data

def documentFunction(function) -> str:
    data = parseDocstringOf(function)
    retval = ""
    retval += "```{py:function} "
    retval += data.docstringSignature
    retval += "\n\n"
    retval += data.brief
    retval += "\n\n"
    retval += data.description
    retval += "\n\n"
    for param in data.params:
        retval += f"\n:param {param.type} {param.name}: {param.brief}"
    if data.returnDescription != "":
        retval += f"\n:return: {data.returnDescription}"
    if data.returnType != "":
        retval += f"\n:rettype: {data.returnType}"
    for note in data.notes:
        if note.type == "note":
            retval += f"\n```{{note}}\n{note.note}\n```"
        elif note.type == "sa":
            retval += f"\n**See also:** {note.note}"
        elif note.type == "deprecated":
            retval += f"\n```{{deprecated}}\n{note.note}\n```"
    retval += "\n```"
    return retval

def documentFunctionsInModule(module) -> str:
    retval = "## Functions\n"

def getAstOfFunction(function) -> str:
    name = function.__qualname__

print(documentFunction(cv2.aruco.calibrateCameraCharucoExtended))
# print(parseDocstringOf(cv2.aruco.calibrateCameraCharucoExtended).__dict__)