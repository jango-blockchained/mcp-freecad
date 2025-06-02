import FreeCAD as App

def serialize_value(value):
    """
    Serializes FreeCAD values to JSON-compatible formats.
    
    Args:
        value: The value to serialize
        
    Returns:
        A JSON-compatible representation of the value
    """
    if isinstance(value, (int, float, str, bool, type(None))):
        return value
    elif isinstance(value, App.Vector):
        return {"x": value.x, "y": value.y, "z": value.z}
    elif isinstance(value, App.Rotation):
        return {
            "Axis": {"x": value.Axis.x, "y": value.Axis.y, "z": value.Axis.z},
            "Angle": value.Angle,
        }
    elif isinstance(value, App.Placement):
        return {
            "Base": serialize_value(value.Base),
            "Rotation": serialize_value(value.Rotation),
        }
    elif isinstance(value, (list, tuple)):
        return [serialize_value(v) for v in value]
    elif hasattr(value, "__module__") and value.__module__ == "FreeCAD.Base" and hasattr(value, "Red"):
        # Handle FreeCAD.Color objects
        return (value.Red, value.Green, value.Blue, value.Alpha)
    else:
        return str(value)


def serialize_shape(shape):
    """
    Serializes a FreeCAD Shape object.
    
    Args:
        shape: The FreeCAD Shape to serialize
        
    Returns:
        Dictionary with shape information
    """
    if shape is None:
        return None
    return {
        "Volume": shape.Volume,
        "Area": shape.Area,
        "VertexCount": len(shape.Vertexes),
        "EdgeCount": len(shape.Edges),
        "FaceCount": len(shape.Faces),
    }


def serialize_view_object(view):
    """
    Serializes a FreeCAD ViewObject.
    
    Args:
        view: The ViewObject to serialize
        
    Returns:
        Dictionary with view object properties
    """
    if view is None:
        return None
    
    result = {
        "Visibility": view.Visibility,
    }
    
    # Add ShapeColor if available
    if hasattr(view, "ShapeColor"):
        result["ShapeColor"] = serialize_value(view.ShapeColor)
    
    # Add Transparency if available
    if hasattr(view, "Transparency"):
        result["Transparency"] = view.Transparency
    
    return result


def serialize_object(obj):
    """
    Serializes a FreeCAD object to a JSON-compatible dictionary.
    
    Args:
        obj: The FreeCAD object to serialize
        
    Returns:
        Dictionary representation of the object
    """
    if isinstance(obj, list):
        return [serialize_object(item) for item in obj]
    elif isinstance(obj, App.Document):
        return {
            "Name": obj.Name,
            "Label": obj.Label,
            "FileName": obj.FileName,
            "Objects": [serialize_object(child) for child in obj.Objects],
        }
    else:
        result = {
            "Name": obj.Name,
            "Label": obj.Label,
            "TypeId": obj.TypeId,
            "Properties": {},
        }
        
        # Add Placement if available
        if hasattr(obj, "Placement"):
            result["Placement"] = serialize_value(obj.Placement)
        
        # Add Shape if available
        if hasattr(obj, "Shape"):
            result["Shape"] = serialize_shape(obj.Shape)
        
        # Add ViewObject if available
        if hasattr(obj, "ViewObject") and obj.ViewObject is not None:
            result["ViewObject"] = serialize_view_object(obj.ViewObject)
        
        # Add all properties
        if hasattr(obj, "PropertiesList"):
            for prop in obj.PropertiesList:
                try:
                    result["Properties"][prop] = serialize_value(getattr(obj, prop))
                except Exception as e:
                    result["Properties"][prop] = f"<error: {str(e)}>"

        return result