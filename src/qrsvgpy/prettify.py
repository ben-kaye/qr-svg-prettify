import xml.etree.ElementTree as ET

from qrsvgpy.utils import (
    DIRECTIONS,
    replace_corner_,
    replace_end_,
    replace_circle_,
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

    registration_mark_(root, 7 * radius, 7 * radius)
    registration_mark_(root, 51 * radius, 7 * radius)
    registration_mark_(root, 7 * radius, 51 * radius)

    xy = [(y, x) for y in range(height) for x in range(width)]
    for y, x in xy:
        rect = qr_code[y][x]
        if rect is None:
            continue

        adjacency_ = adjacency(y, x)
        num_adjacent = sum(adjacency_)
        if not num_adjacent:
            replace_circle_(root, rect)
            continue
        # Check if the pixel is adjacent to only one other pixel

        if num_adjacent == 1:
            # Get the direction of the adjacent pixelz
            adjacent_dir_index = adjacency_.index(True)
            replace_end_(root, rect, adjacent_dir_index)

            continue

        if num_adjacent == 2:
            dirs = [k for k, v in enumerate(adjacency_) if v]
            replace_corner_(root, rect, dirs[0], dirs[1])
            continue


def read_qr_svg(svg_path):
    objs, svg_treeroot = extract_rectangles_from_svg(svg_path)
    bitmap, qr_code = create_bitmap_from_rectangles(objs)
    prettify_qr_svg_(svg_treeroot, qr_code)

    return svg_treeroot, bitmap
