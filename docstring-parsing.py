import cv2
from enum import Enum
import inspect
from typing import Callable
import typeshed_client
import ast
from pathlib import Path

LL_DEBUG_OVER = 1
LL_DEBUG_SPECIFIC = 2
logLevel = LL_DEBUG_SPECIFIC

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

class FunctionType(Enum):
    UNKNOWN = 0
    FUNCTION = 1
    INSTANCE_METHOD = 2
    CLASS_METHOD = 3
    STATIC_METHOD = 4

class FunctionData:
    def __init__(self):
        self.function: Callable = None
        self.name: str = ""
        self.unqualifiedName: str = ""
        self.brief: str = ""
        self.docstringSignature: str = ""
        self.astSignature: str = ""
        self.params: dict[str, ParamData] = dict()
        self.notes: list[NoteData] = []
        self.description: str = ""
        self.returnDescription: str = ""
        self.returnType: str = "object"
        self.type: FunctionType = FunctionType.UNKNOWN

    def __repr__(self):
        return str(self.__dict__)
        # return str(self.params)

class AttributeData:
    def __init__(self):
        self.name: str = ""
        self.unqualifiedName: str = ""
        self.brief: str = ""
        self.type: str = ""
        self.value: str = None

    def __repr__(self):
        return str(self.__dict__)

class ClassData:
    def __init__(self):
        self.theClass: object = None
        self.name: str = ""
        self.unqualifiedName: str = ""
        self.brief: str = ""
        self.description: str = ""
        self.notes: list[NoteData] = []
        self.classMethods: list[FunctionData] = []
        self.staticMethods: list[FunctionData] = []
        self.instanceMethods: list[FunctionData] = []
        self.instanceAttributes: list[AttributeData] = []
        
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

def parseDocstringOfClass(theClass: Callable, data: FunctionData):
    retval = ""
    if not theClass.__doc__:
        return
    lines = theClass.__doc__.splitlines()
    data.docstringSignature = lines.pop(0)
    curData: Reference = None
    for line in lines:
        line = line.lstrip(" .*")
        line = line.strip()
        line = line.replace("\\f$", "$")
        line = line.replace("\\f[", "$")
        line = line.replace("\\f]", "$")
        # print(line)
        if line.startswith("@brief "):
            data.brief = line.removeprefix("@brief ")
            curData = AttributeReference(data, "brief")
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
        elif line.startswith("@see "):
            note = NoteData()
            note.type = "sa"
            note.note = line.removeprefix("@see ")
            data.notes.append(note)
            curData = AttributeReference(note, "note")
        elif line.startswith("@deprecated "):
            note = NoteData()
            note.type = "deprecated"
            note.note = line.removeprefix("@deprecated ")
            data.notes.append(note)
            curData = AttributeReference(note, "note")
    # return data

def parseDocstringOfFunction(function: Callable, data: FunctionData):
    if not function.__doc__:
        return
    retval = ""
    lines = function.__doc__.splitlines()
    if "Initialize self.  See help(type(self)) for accurate signature." not in lines[0]:
        data.docstringSignature = lines.pop(0)
    curData: Reference = None
    inCodeBlock = False
    # TODO: If the line doesn't start with ".", then we need to return multiple functions;
    #     the original function was overloaded
    for line in lines:
        if line.startswith(".   "):
            line = line.removeprefix(".   ")
            # line = line.lstrip(".*")
            # line = line.strip()
            line = line.replace("\\f$", "$")
            line = line.replace("\\f[", "$")
            line = line.replace("\\f]", "$")
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
            elif line.startswith("@param[in]"):
                splitline = line.split()
                paramName = splitline[1]
                if paramName not in data.params:
                    data.params[paramName] = ParamData()
                param = data.params[paramName]
                param.name = splitline[1]
                param.brief = "[in] " + " ".join(splitline[2:])
                curData = AttributeReference(param, "brief")
                # data.params.append(param)
            elif line.startswith("@param[out]"):
                splitline = line.split()
                paramName = splitline[1]
                if paramName not in data.params:
                    data.params[paramName] = ParamData()
                param = data.params[paramName]
                param.name = splitline[1]
                param.brief = "[out] " + " ".join(splitline[2:])
                curData = AttributeReference(param, "brief")
                # data.params.append(param)
            elif line.startswith("@return "):
                data.returnDescription = line.removeprefix("@return ")
                curData = AttributeReference(data, "returnDescription")
            elif line.startswith("@returns "):
                data.returnDescription = line.removeprefix("@returns ")
                curData = AttributeReference(data, "returnDescription")
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
            elif line.startswith("@see "):
                note = NoteData()
                note.type = "sa"
                note.note = line.removeprefix("@see ")
                data.notes.append(note)
                curData = AttributeReference(note, "note")
            elif line.startswith("@deprecated "):
                note = NoteData()
                note.type = "deprecated"
                note.note = line.removeprefix("@deprecated ")
                data.notes.append(note)
                curData = AttributeReference(note, "note")
            elif line.startswith("@code{."):
                # if logLevel >= LL_DEBUG_SPECIFIC: print("Code block found!")
                if curData is None:
                    curData = AttributeReference(data, "description")
                    data.description += "\n"
                codelang = line.removeprefix("@code{.").removesuffix("}")
                curData.setValue(curData.getValue() + f"\n```{codelang}\n")
                inCodeBlock = True
            elif line.startswith("@code"):
                # if logLevel >= LL_DEBUG_SPECIFIC: print("Code block found!")
                if curData is None:
                    curData = AttributeReference(data, "description")
                    data.description += "\n"
                curData.setValue(curData.getValue() + "\n```c++\n")
                inCodeBlock = True
            elif line.startswith("@endcode"):
                if curData is None:
                    curData = AttributeReference(data, "description")
                    data.description += "\n"
                curData.setValue(curData.getValue() + "```\n")
                inCodeBlock = False
            elif line == "":
                curData = None
            else:
                if curData is None:
                    curData = AttributeReference(data, "description")
                    data.description += "\n"
                curData.setValue(curData.getValue() + line + "\n")
    # return data

def documentFunctionNamed(name) -> str:
    # print(f"Documenting {name}...")
    function = eval(name)
    data = FunctionData()
    data.name = name
    data.type = FunctionType.FUNCTION
    parseDocstringOfFunction(function, data)
    parseAstOfFunction(name, data)
    return documentFunction(function, data)

def documentFunction(function: Callable, data: FunctionData) -> str:
    retval = ""
    if data.type == FunctionType.FUNCTION:
        retval += "````{py:function} "
    else:
        retval += "````{py:method} "
    if data.docstringSignature:
        retval += data.docstringSignature
    else:
        # retval += data.unqualifiedName + str(inspect.signature(function))
        retval += data.astSignature
    retval += "\n"
    if data.type == FunctionType.FUNCTION or data.type == FunctionType.INSTANCE_METHOD:
        retval += "\n"
    elif data.type == FunctionType.CLASS_METHOD:
        retval += ":classmethod:\n"
    elif data.type == FunctionType.STATIC_METHOD:
        retval += ":staticmethod:\n"
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
        retval += f"\n:rtype: {data.returnType}"
    retval += "\n````"
    return retval


def documentClassNamed(name) -> str:
    theClass = eval(name)
    data = ClassData()
    data.name = name
    data.theClass = theClass
    parseDocstringOfClass(theClass, data)
    parseAstOfClass(name, data)
    retval = ""
    retval += f"`````{{py:class}} {data.unqualifiedName}\n"
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
    for funcdata in [*data.classMethods, *data.instanceMethods, *data.staticMethods]:
        funcdata.function = getattr(theClass, funcdata.unqualifiedName)
        parseDocstringOfFunction(funcdata.function, funcdata)
        # parseAstOfFunction(funcdata.name, funcdata)
        retval += documentFunction(funcdata.function, funcdata) + "\n\n"
    for attrdata in data.instanceAttributes:
        retval += documentAttribute(attrdata) + "\n\n"
    retval += "\n`````"
    return retval

def documentAttributeNamed(name: str) -> str:
    attrdata = AttributeData()
    attrdata.name = name
    parseAstOfAttribute(name, attrdata)
    return documentAttribute(attrdata)

def documentAttribute(attrdata: AttributeData) -> str:
    retval = f"```{{py:attribute}} {attrdata.unqualifiedName}\n"
    if attrdata.type: retval += f":type: {attrdata.type}\n"
    if attrdata.value: retval += f":value: {attrdata.value}\n"
    retval += "```"
    return retval



def documentFunctionsInModule(moduleName) -> str:
    module = eval(moduleName)
    functions: list[tuple[str, Callable]] = inspect.getmembers(module, lambda x: callable(x) and not inspect.isclass(x))
    # print(functions)
    retval = "## Functions\n"
    for name, function in functions:
        if logLevel >= LL_DEBUG_OVER: print(f"Documenting function {moduleName}.{name}...")
        retval += documentFunctionNamed(moduleName + "." + name)
        retval += "\n\n\n"
    return retval

def documentClassesInModule(moduleName) -> str:
    module = eval(moduleName)
    classes: list[tuple[str, Callable]] = inspect.getmembers(module, inspect.isclass)
    # print(functions)
    retval = "## Classes\n"
    for name, theClass in classes:
        if logLevel >= LL_DEBUG_OVER: print(f"Documenting class {moduleName}.{name}...")
        retval += documentClassNamed(moduleName + "." + name)
        retval += "\n\n\n"
    return retval

def documentAttributesInModule(moduleName) -> str:
    module = eval(moduleName)
    attributes: list[tuple[str, object]] = inspect.getmembers(module, lambda x: not callable(x))
    # print(functions)
    retval = "## Attributes\n"
    for name, value in attributes:
        if logLevel >= LL_DEBUG_OVER: print(f"Documenting attribute {moduleName}.{name}...")
        retval += documentAttributeNamed(moduleName + "." + name)
        retval += "\n\n\n"
    return retval

def documentModule(moduleName, documentAttributes: bool = False) -> str:
    retval = f"# `{moduleName}`\n"
    retval += f"```{{py:module}} {moduleName}\n{eval(moduleName).__doc__}\n```\n"
    if documentAttributes:
        if logLevel >= LL_DEBUG_OVER: print(f"Documenting attributes in {moduleName}...")
        retval += documentAttributesInModule(moduleName) + "\n"
    if logLevel >= LL_DEBUG_OVER: print(f"Documenting classes in {moduleName}...")
    retval += documentClassesInModule(moduleName) + "\n"
    if logLevel >= LL_DEBUG_OVER: print(f"Documenting functions in {moduleName}...")
    retval += documentFunctionsInModule(moduleName) + "\n"
    return retval

def astOf(name) -> ast.AST:
    resolver = typeshed_client.Resolver()
    nameInfo = resolver.get_fully_qualified_name(name)
    if nameInfo is None or not hasattr(nameInfo, "ast"):
        return None
    if isinstance(nameInfo.ast, typeshed_client.OverloadedName):
        return nameInfo.ast.definitions[0]
    return nameInfo.ast

def parseAstOfFunction(name: str, data: FunctionData):
    functionAST: ast.FunctionDef = astOf(name)
    if functionAST is None:
        return
    parseFunctionAst(functionAST, data)

def parseFunctionAst(functionAST: ast.FunctionDef, data: FunctionData):
    for arg in functionAST.args.args:
        paramName = arg.arg
        if paramName not in data.params:
            data.params[paramName] = ParamData()
        param = data.params[paramName]
        param.name = paramName
        try:
            param.type = ast.unparse(arg.annotation)
        except: pass
    if data.type != FunctionType.FUNCTION:
        for decorator in functionAST.decorator_list:
            decoratorName = ast.unparse(decorator)
            if decoratorName == "staticmethod":
                data.type = FunctionType.STATIC_METHOD
                break
            elif decoratorName == "classmethod":
                data.type = FunctionType.CLASS_METHOD
                break
            else:
                data.type = FunctionType.INSTANCE_METHOD
    data.returnType = ast.unparse(functionAST.returns)
    data.astSignature = data.unqualifiedName + "(" + ast.unparse(functionAST.args) + ")"

def parseAstOfAttribute(name: str, attrdata: AttributeData):
    attr: ast.FunctionDef = astOf(name)
    if attr is None:
        return
    parseAttributeAst(attr, attrdata)

def parseAttributeAst(attr: ast.AnnAssign, attrdata: AttributeData):
    # attrdata.name = name + "." + ast.unparse(attr.target)
    attrdata.unqualifiedName = ast.unparse(attr.target)
    attrdata.type = ast.unparse(attr.annotation)
    try:
        attrdata.value = ast.unparse(attr.value)
    except: pass

def parseAstOfClass(name: str, data: ClassData):
    classAST: ast.ClassDef = astOf(name)
    if classAST is None:
        return
    data.unqualifiedName = classAST.name
    for attr in classAST.body:
        if isinstance(attr, ast.AnnAssign):
            attrdata = AttributeData()
            parseAttributeAst(attr, attrdata)
            data.instanceAttributes.append(attrdata)
        elif isinstance(attr, ast.FunctionDef):
            funcdata = FunctionData()
            funcdata.unqualifiedName = attr.name
            funcdata.name = name + "." + attr.name
            parseFunctionAst(attr, funcdata)
            if funcdata.type == FunctionType.INSTANCE_METHOD:
                data.instanceMethods.append(funcdata)
            elif funcdata.type == FunctionType.CLASS_METHOD:
                data.classMethods.append(funcdata)
            else:
                data.staticMethods.append(funcdata)
            pass
    return

def makeIndexMD(modules: list[str]):
    retval = """<!-- Generated by opencv-doc-parser -->
# OpenCV Python API

```{toctree}
---
caption: Contents
titlesonly: true
---
"""
    for moduleName in modules:
        retval += f"{moduleName}.md\n"
    retval += "```\n"
    return retval

# print(documentFunction(cv2.aruco.calibrateCameraCharucoExtended))
# print(documentFunction("cv2.aruco.calibrateCameraCharucoExtended"))
# print(documentModule("cv2.aruco"))
# print(documentClassNamed("cv2.aruco.Dictionary"))
# print(astOfFunction("cv2.aruco.calibrateCameraCharucoExtended"))

# Not included:
# * cv2.alphamat - doesn't exist
# * cv2.bgsegm - doesn't exist
# * cv2.bioinspired - doesn't exist
# * cv2.cann - doesn't exist
# * cv2.ccalib - doesn't exist
# * cv2.ccm - doesn't exist
# * cv2.colored_kinfu - doesn't exist
# * cv2.cudacodec - doesn't exist
# * cv2.cudev - doesn't exist
# * cv2.datasets - doesn't exist
# * cv2.details - doesn't exist
# * cv2.directx - doesn't exist
# * cv2.dnn_objdetect - doesn't exist
# * cv2.dnn_superres - doesn't exist

modules = ["cv2.aruco", "cv2.barcode", "cv2.cuda", "cv2.dnn", "cv2"]
for moduleName in modules:
    print(f"Parsing {moduleName}...")
    with open(Path(__file__).parent.parent / "opencv-python-docs" / "source" / f"{moduleName}.md", "w") as file:
        file.write(documentModule(moduleName, documentAttributes=(moduleName != "cv2")))

print("Making index.md...")
with open(Path(__file__).parent.parent / "opencv-python-docs" / "source" / "index.md", "w") as file:
    file.write(makeIndexMD(modules))

print("Done.")

# print(documentFunctionNamed("cv2.subtract"))