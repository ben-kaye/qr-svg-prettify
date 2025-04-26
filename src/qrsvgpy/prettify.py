import xml.etree.ElementTree as ET

from qrsvgpy.utils import (
    DIRECTIONS,
    replace_corner,
    replace_end,
    rect_to_circle,
    registration_mark_,
)


def extract_rectangles_from_svg(
    svg_path, side=16, remove_groups=True
) -> tuple[list[tuple[int, int]], ET.Element]:
    # Parse the SVG file
    tree = ET.parse(svg_path)
    root = tree.getroot()

    objs = []
    # delete top level groups
    if remove_groups:
        for child in root.findall(".//{http://www.w3.org/2000/svg}g"):
            root.remove(child)

    for rect in root.findall(".//{http://www.w3.org/2000/svg}rect"):
        x = int(float(rect.get("x", 0)))
        y = int(float(rect.get("y", 0)))
        width = int(float(rect.get("width", 0)))
        height = int(float(rect.get("height", 0)))

        # Only consider 16x16 rectangles
        if width == side and height == side:
            xy = (x // side, y // side)

            objs.append((xy, rect))

    return objs, root


def create_bitmap_from_rectangles(xy_objects):
    if not xy_objects:
        return [], []
    xy, rects = zip(*xy_objects)
    x, y = zip(*xy)
    shape_x = max(x) + 1
    shape_y = max(y) + 1

    # Create a bitmap filled with zeros
    bitmap = [[0 for _ in range(shape_x)] for _ in range(shape_y)]
    qr_code = [[None for _ in range(shape_x)] for _ in range(shape_y)]

    # Fill in the bitmap with 1s where rectangles are located
    for (x, y), obj in xy_objects:
        bitmap[y][x] = 1
        qr_code[y][x] = obj
    return bitmap, qr_code


def prettify_qr_svg_(root, qr_code, side=16):
    """
    Process the SVG by converting isolated rectangles to circles.
    An isolated rectangle is one with no adjacent rectangles in any direction.
    """
    height = len(qr_code)
    width = len(qr_code[0]) if height > 0 else 0
    radius = side // 2

    def adjacency(y, x):
        adjacency = [False for _ in DIRECTIONS]
        for k, (dy, dx) in enumerate(DIRECTIONS):
            ny, nx = y + dy, x + dx
            if 0 <= ny < height and 0 <= nx < width and qr_code[ny][nx] is not None:
                adjacency[k] = True
        return adjacency

    center_reg = 7
    offset = 2 * height - center_reg
    registration_mark_(root, center_reg * radius, center_reg * radius)
    registration_mark_(root, offset * radius, center_reg * radius)
    registration_mark_(root, center_reg * radius, offset * radius)

    xy = [(y, x) for y in range(height) for x in range(width)]

    lone_circle_group = ET.Element("{http://www.w3.org/2000/svg}g")

    for y, x in xy:
        rect = qr_code[y][x]
        if rect is None:
            continue

        adjacency_ = adjacency(y, x)
        num_adjacent = sum(adjacency_)
        match num_adjacent:
            case 0:
                circle = rect_to_circle(rect)
                lone_circle_group.append(circle)
                root.remove(rect)

            case 1:
                # Get the direction of the adjacent pixelz
                adjacent_dir_index = adjacency_.index(True)
                new_rect, circle = replace_end(rect, adjacent_dir_index)
                root.append(circle)
                root.append(new_rect)
                root.remove(rect)

            case 2:
                dirs = [k for k, v in enumerate(adjacency_) if v]
                result = replace_corner(rect, dirs[0], dirs[1])

                if result is None:
                    continue
                polygon, circle = result
                root.append(circle)
                root.append(polygon)
                root.remove(rect)

    root.append(lone_circle_group)


def read_qr_svg(svg_path):
    objs, svg_treeroot = extract_rectangles_from_svg(svg_path)
    bitmap, qr_code = create_bitmap_from_rectangles(objs)
    prettify_qr_svg_(svg_treeroot, qr_code)

    return svg_treeroot, bitmap
