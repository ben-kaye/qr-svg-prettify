from qrsvgpy.prettify import read_qr_svg
from xml.etree import ElementTree as ET


def main(svg_path):
    svg_treeroot, bitmap = read_qr_svg(svg_path)

    # Write the XML ElementTree to the output file
    # Use encoding and xml_declaration to ensure proper XML formatting
    ET.ElementTree(svg_treeroot).write(
        "animodel-github-processed.svg",
        encoding="utf-8",
        xml_declaration=True,
        method="xml",
    )

    # Display the bitmap
    from matplotlib import pyplot as plt
    import numpy as np

    bitmap = np.array(bitmap)
    if bitmap.size > 0:
        plt.figure(figsize=(5, 5))
        plt.imshow(bitmap, cmap="binary", interpolation="nearest")
        plt.title("QR code 28x28")
        plt.colorbar(label="Presence of rectangle")
        plt.savefig("rectangle_bitmap.png")
        plt.show()
    else:
        print("No rectangles found to create bitmap")


if __name__ == "__main__":
    main("animodel-github-inp.svg")
