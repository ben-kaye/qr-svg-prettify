from xml.etree import ElementTree as ET
from enum import IntEnum

DIRECTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))


class Direction(IntEnum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


side = 16
radius = side // 2


def replace_circle_(root: ET.Element, rect: ET.Element):
    # Get the original rectangle's position
    rect_x = float(rect.get("x", 0))
    rect_y = float(rect.get("y", 0))
    rect_width = float(rect.get("width", 0))

    # Create a circle element with the same attributes
    circle = ET.Element("{http://www.w3.org/2000/svg}circle")
    circle.set("cx", str(rect_x + radius))  # Center x
    circle.set("cy", str(rect_y + radius))  # Center y
    circle.set("r", str(radius))  # Radius 8

    # Copy any other attributes from rectangle to circle
    for attr, value in rect.attrib.items():
        circle.set(attr, value)

    root.remove(rect)
    root.append(circle)


def replace_end_(root: ET.Element, rect: ET.Element, dir_index: int):
    # Create a half circle that intersects with the rectangle
    rect_x = float(rect.get("x", 0))
    rect_y = float(rect.get("y", 0))

    # Create a circle element
    circle = ET.Element("{http://www.w3.org/2000/svg}circle")
    circle.set("cx", str(rect_x + radius))  # Center x
    circle.set("cy", str(rect_y + radius))  # Center y
    circle.set("r", str(radius))  # Radius 8

    # Create a rectangle element that covers half of the original rectangle
    # oriented toward the adjacent pixel (dx, dy)
    rectangle = ET.Element("{http://www.w3.org/2000/svg}rect")
    rectangle.set("width", str(side))
    rectangle.set("height", str(side))
    rectangle.set("style", "fill:black")
    rectangle.set("x", str(rect_x))
    rectangle.set("y", str(rect_y))

    vertical = dir_index == Direction.RIGHT or dir_index == Direction.LEFT

    if vertical:
        rectangle.set("width", str(radius))
        if dir_index == Direction.RIGHT:
            rectangle.set("x", str(rect_x + radius))
        else:
            rectangle.set("x", str(rect_x))
    else:
        rectangle.set("height", str(radius))
        if dir_index == Direction.DOWN:
            rectangle.set("y", str(rect_y + radius))
        else:
            rectangle.set("y", str(rect_y))

    # Copy any other attributes from original rectangle
    for attr, value in rect.attrib.items():
        if attr not in ["x", "y", "width", "height", "style"]:
            circle.set(attr, value)
            rectangle.set(attr, value)

    # Add both shapes to the group
    root.append(rectangle)
    root.append(circle)

    # Remove the original rectangle and add the group
    root.remove(rect)


def replace_corner_(
    root: ET.Element, rect: ET.Element, dir_index_1: int, dir_index_2: int
):
    # find the corner with no adjacent pixels
    # create a circle at the corner
    # replace rect with a triangle cut out from this corner, side=8,8
    # create a group element to contain both shapes

    # Get rectangle attributes
    rect_x = int(rect.get("x"))
    rect_y = int(rect.get("y"))
    side = int(rect.get("width"))  # Assuming width and height are the same (16x16)
    radius = side // 2  # Radius is half the side length

    corner_x = rect_x
    corner_y = rect_y

    has_up = dir_index_1 == Direction.UP or dir_index_2 == Direction.UP
    has_right = dir_index_1 == Direction.RIGHT or dir_index_2 == Direction.RIGHT

    # if both up/down or left/right, then return rect
    same_dir = dir_index_1 % 2 == dir_index_2 % 2
    if same_dir:
        return

    circle_origin = (rect_x + radius, rect_y + radius)
    # coord starts in top left therefore
    if has_up:
        if has_right:
            # bottom left!
            corner_x = rect_x
            corner_y = rect_y + side
        else:  # has_left
            # bottom right!
            corner_x = rect_x + side
            corner_y = rect_y + side
    else:  # has_down
        if has_right:
            # top left!
            corner_x = rect_x
            corner_y = rect_y
        else:  # has_left
            # top right!
            corner_x = rect_x + side
            corner_y = rect_y

    # Create a circle element at the corner
    circle = ET.Element("{http://www.w3.org/2000/svg}circle")
    circle.set("cx", str(circle_origin[0]))
    circle.set("cy", str(circle_origin[1]))
    circle.set("r", str(radius))

    # Create a polygon element for the rectangle with the corner cut out
    polygon = ET.Element("{http://www.w3.org/2000/svg}polygon")

    # Define the points for the polygon (rectangle with one corner cut out)
    points = []

    rect_corners = [
        (rect_x, rect_y),  # top-left
        (rect_x + side, rect_y),  # top-right
        (rect_x + side, rect_y + side),  # bottom-right
        (rect_x, rect_y + side),  # bottom-left
    ]

    # Find which corner needs to be replaced with arc points
    corner_index = -1
    for i, (cx, cy) in enumerate(rect_corners):
        if cx == corner_x and cy == corner_y:
            corner_index = i
            break

    # Add all corners except the one that needs to be replaced
    for i, (cx, cy) in enumerate(rect_corners):
        if i != corner_index:
            points.append(f"{cx},{cy}")

    # Calculate the two points where the circle intersects the rectangle
    # These depend on which corner we're replacing
    if corner_x == rect_x and corner_y == rect_y:  # top-left
        points.insert(0, f"{rect_x + radius},{rect_y}")
        points.append(f"{rect_x},{rect_y + radius}")
    elif corner_x == rect_x + side and corner_y == rect_y:  # top-right
        points.insert(1, f"{rect_x + side},{rect_y + radius}")
        points.insert(1, f"{rect_x + side - radius},{rect_y}")
    elif corner_x == rect_x + side and corner_y == rect_y + side:  # bottom-right
        points.insert(2, f"{rect_x + side - radius},{rect_y + side}")
        points.insert(2, f"{rect_x + side},{rect_y + side - radius}")
    elif corner_x == rect_x and corner_y == rect_y + side:  # bottom-left
        points.append(f"{rect_x + radius},{rect_y + side}")
        points.append(f"{rect_x},{rect_y + side - radius}")

    polygon.set("points", " ".join(points))
    polygon.set("style", "fill:black")

    # Copy any other attributes from original rectangle
    for attr, value in rect.attrib.items():
        if attr not in ["x", "y", "width", "height", "style"]:
            circle.set(attr, value)
            polygon.set(attr, value)

    root.append(polygon)
    root.append(circle)
    root.remove(rect)


def registration_mark_(
    root: ET.Element, cx: int | float, cy: int | float, size: int = 7
):
    # create a circle at the center of the rectangle
    # Create a group for the registration mark
    group = ET.Element("{http://www.w3.org/2000/svg}g")

    # Create outer circle
    circle = ET.Element("{http://www.w3.org/2000/svg}circle")
    circle.set("cx", str(cx))
    circle.set("cy", str(cy))
    circle.set("r", str(size * radius))
    circle.set("fill", "black")
    group.append(circle)

    # Create a mask for the inner circle (to subtract from outer)
    mask_id = f"mask_{cx}_{cy}"
    mask = ET.Element("{http://www.w3.org/2000/svg}mask")
    mask.set("id", mask_id)

    # White background for the mask
    mask_bg = ET.Element("{http://www.w3.org/2000/svg}rect")
    mask_bg.set("x", str(cx - size * side))
    mask_bg.set("y", str(cy - size * side))
    mask_bg.set("width", str(2 * size * side))
    mask_bg.set("height", str(2 * size * side))
    mask_bg.set("fill", "white")
    mask.append(mask_bg)

    # Inner circle (black in mask means transparent in result)
    mask_circle = ET.Element("{http://www.w3.org/2000/svg}circle")
    mask_circle.set("cx", str(cx))
    mask_circle.set("cy", str(cy))
    mask_circle.set("r", str((size - 2) * radius))
    mask_circle.set("fill", "black")
    mask.append(mask_circle)

    # Add mask to defs
    defs = root.find(".//{http://www.w3.org/2000/svg}defs")
    if defs is None:
        defs = ET.Element("{http://www.w3.org/2000/svg}defs")
        root.insert(0, defs)
    defs.append(mask)

    # Apply mask to outer circle
    circle.set("mask", f"url(#{mask_id})")

    # Create innermost circle
    inner_circle = ET.Element("{http://www.w3.org/2000/svg}circle")
    inner_circle.set("cx", str(cx))
    inner_circle.set("cy", str(cy))
    inner_circle.set("r", str((size - 4) * radius))
    inner_circle.set("fill", "black")
    group.append(inner_circle)

    # Add the group to the root
    root.append(group)
