from pathlib import Path
from typing import List, Tuple
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from svgpathtools import parse_path

from app.models.svg_file import SVGPath

@dataclass
class SVGData:
    paths: List[SVGPath]
    width: float
    height: float

def extract_coordinates_from_path(d: str, num_points: int = 100) -> List[Tuple[float, float]]:
    """Extract (x, y) coordinates from an SVG path 'd' attribute."""
    if not d or not d.strip():
        return []
    
    try:
        path = parse_path(d)
        if path.length() == 0:
            return []
        
        coordinates = []
        for i in range(num_points + 1):
            t = i / num_points
            point = path.point(t)
            coordinates.append((point.real, point.imag))
        
        return coordinates
    except Exception as e:
        return []

def parse_svg_file(svg_path: Path) -> SVGData:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}
    
    width = 300.0
    height = 200.0
    
    width_attr = root.get('width')
    height_attr = root.get('height')
    
    if width_attr:
        width = float(width_attr.replace('mm', '').replace('px', ''))
    if height_attr:
        height = float(height_attr.replace('mm', '').replace('px', ''))
    
    viewbox = root.get('viewBox')
    if viewbox and not width_attr:
        parts = viewbox.split()
        if len(parts) == 4:
            width = float(parts[2])
            height = float(parts[3])
    
    paths = []
    path_id_counter = 0
    
    for elem in root.iter():
        tag_name = elem.tag.split('}')[-1]
        
        if tag_name == 'path':
            d = elem.get('d', '')
            if not d:
                continue
            
            path_id_counter += 1
            path_id = f"path_{path_id_counter:03d}"
            
            style = elem.get('style', '')
            stroke = elem.get('stroke', '')
            fill = elem.get('fill', '')
            
            color = extract_color(style, stroke, fill)
            action = detect_action_from_color(color)
            
            paths.append(SVGPath(
                path_id=path_id,
                d=d,
                color=color,
                detected_action=action
            ))
        
        elif tag_name in ['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon']:
            path_id_counter += 1
            path_id = f"path_{path_id_counter:03d}"
            
            d = convert_shape_to_path(elem, tag_name)
            if not d:
                continue
            
            style = elem.get('style', '')
            stroke = elem.get('stroke', '')
            fill = elem.get('fill', '')
            
            color = extract_color(style, stroke, fill)
            action = detect_action_from_color(color)
            
            paths.append(SVGPath(
                path_id=path_id,
                d=d,
                color=color,
                detected_action=action
            ))
    
    return SVGData(paths=paths, width=width, height=height)

def extract_color(style: str, stroke: str, fill: str) -> str:
    if 'stroke:' in style:
        for part in style.split(';'):
            if 'stroke:' in part:
                color = part.split(':')[1].strip()
                if color and color != 'none':
                    return color
    
    if stroke and stroke != 'none':
        return stroke
    
    if fill and fill != 'none':
        return fill
    
    return '#000000'

def detect_action_from_color(color: str) -> str:
    color = color.lower().replace('#', '')
    
    if color in ['ff0000', 'red', 'rgb(255,0,0)', 'rgb(255, 0, 0)']:
        return 'cut'
    
    if color in ['0000ff', 'blue', 'rgb(0,0,255)', 'rgb(0, 0, 255)']:
        return 'engrave'
    
    if len(color) == 6:
        try:
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            
            if r >= 245 and g <= 10 and b <= 10:
                return 'cut'
            
            if r <= 10 and g <= 10 and b >= 245:
                return 'engrave'
        except:
            pass
    
    return 'ignore'

def convert_shape_to_path(elem, tag_name: str) -> str:
    if tag_name == 'rect':
        x = float(elem.get('x', 0))
        y = float(elem.get('y', 0))
        width = float(elem.get('width', 0))
        height = float(elem.get('height', 0))
        return f"M {x} {y} L {x+width} {y} L {x+width} {y+height} L {x} {y+height} Z"
    
    elif tag_name == 'circle':
        cx = float(elem.get('cx', 0))
        cy = float(elem.get('cy', 0))
        r = float(elem.get('r', 0))
        return f"M {cx-r} {cy} A {r} {r} 0 1 1 {cx-r} {cy+0.01} Z"
    
    elif tag_name == 'line':
        x1 = float(elem.get('x1', 0))
        y1 = float(elem.get('y1', 0))
        x2 = float(elem.get('x2', 0))
        y2 = float(elem.get('y2', 0))
        return f"M {x1} {y1} L {x2} {y2}"
    
    return ""
