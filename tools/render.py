"""Рендер референсов Arvello: z-буфер без внешних 3D-библиотек.

Модель = список деталей-параллелепипедов (мм). Из одной геометрии получаем:
  - clay.png  — «глиняный» рендер с цветами материалов (референс формы и ракурса)
  - line.png  — контурный рисунок (референс для структурного контроля)
  - mask.png  — силуэт изделия (для прозрачного фона и вырезки слоёв)
  - scheme.png — ортогональный чертёж с размерами (для сайта и цеха)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


@dataclass
class Part:
    name: str
    x0: float
    y0: float
    z0: float
    x1: float
    y1: float
    z1: float
    color: tuple  # RGB 0..255
    group: str = ""  # логическая группа: frame, top, base, headboard ...

    def corners(self):
        xs, ys, zs = (self.x0, self.x1), (self.y0, self.y1), (self.z0, self.z1)
        return np.array([[x, y, z] for x in xs for y in ys for z in zs], float)

    def faces(self):
        """6 граней: (4 вершины по кругу, нормаль)."""
        x0, y0, z0, x1, y1, z1 = self.x0, self.y0, self.z0, self.x1, self.y1, self.z1
        return [
            ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),  # перед
            ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], (0, 1, 0)),   # зад
            ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], (-1, 0, 0)),  # лево
            ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0)),   # право
            ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1)),   # верх
            ([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], (0, 0, -1)),  # низ
        ]


@dataclass
class Glow:
    """Светящееся пятно на полу (LED-подсветка), рисуется под геометрией."""
    x0: float
    y0: float
    x1: float
    y1: float
    color: tuple
    blur_mm: float = 250


@dataclass
class Model:
    parts: list
    glows: list = field(default_factory=list)
    dims: list = field(default_factory=list)  # доп. размеры для чертежа

    def bbox(self):
        pts = np.vstack([p.corners() for p in self.parts])
        return pts.min(0), pts.max(0)


# ---------------------------------------------------------------- камера

def camera_basis(target, az_deg, el_deg, dist):
    az, el = math.radians(az_deg), math.radians(el_deg)
    cam = np.array(target, float) + dist * np.array(
        [-math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)])
    f = np.array(target, float) - cam
    f /= np.linalg.norm(f)
    up = np.array([0, 0, 1.0])
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return cam, r, u, f


def project_persp(pts, cam, r, u, f):
    v = pts - cam
    x, y, z = v @ r, v @ u, v @ f
    return np.stack([x / z, y / z], 1), z


def project_ortho(pts, view):
    if view == "front":   # смотрим с -y: x вправо, z вверх
        return np.stack([pts[:, 0], pts[:, 2]], 1), pts[:, 1] + 1e5
    if view == "side":    # смотрим справа (+x): y вправо... слева направо: перед -> зад
        return np.stack([pts[:, 1], pts[:, 2]], 1), 1e5 - pts[:, 0]
    if view == "top":     # сверху: x вправо, y вверх
        return np.stack([pts[:, 0], pts[:, 1]], 1), 1e5 - pts[:, 2]
    raise ValueError(view)


# ---------------------------------------------------------------- растеризация

def _raster(tris, W, H):
    """tris: list of (P[3,2] экранные px, Z[3] глубина>0, face_id).
    Возвращает id-буфер и буфер 1/z."""
    zbuf = np.zeros((H, W), np.float32)      # храним 1/z, больше = ближе
    idbuf = np.full((H, W), -1, np.int32)
    for P, Z, fid in tris:
        xmin = max(int(math.floor(P[:, 0].min())), 0)
        xmax = min(int(math.ceil(P[:, 0].max())), W - 1)
        ymin = max(int(math.floor(P[:, 1].min())), 0)
        ymax = min(int(math.ceil(P[:, 1].max())), H - 1)
        if xmin > xmax or ymin > ymax:
            continue
        xs = np.arange(xmin, xmax + 1) + 0.5
        ys = np.arange(ymin, ymax + 1) + 0.5
        gx, gy = np.meshgrid(xs, ys)
        (x0, y0), (x1, y1), (x2, y2) = P
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-9:
            continue
        w0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / den
        w1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        invz = w0 / Z[0] + w1 / Z[1] + w2 / Z[2]
        sub_z = zbuf[ymin:ymax + 1, xmin:xmax + 1]
        sub_id = idbuf[ymin:ymax + 1, xmin:xmax + 1]
        upd = inside & (invz > sub_z)
        sub_z[upd] = invz[upd]
        sub_id[upd] = fid
    return idbuf, zbuf


def _edges(idbuf, thickness=1):
    e = np.zeros(idbuf.shape, bool)
    e[:, :-1] |= idbuf[:, :-1] != idbuf[:, 1:]
    e[:-1, :] |= idbuf[:-1, :] != idbuf[1:, :]
    if thickness > 1:
        if thickness % 2 == 0:
            thickness += 1
        img = Image.fromarray((e * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(thickness))
        e = np.array(img) > 0
    return e


LIGHT = np.array([-0.45, -0.65, 0.62])
LIGHT /= np.linalg.norm(LIGHT)


def render(model: Model, *, az, el, size=(1000, 1250), ss=2, fill=0.82,
           focus_box=None, dist_factor=2.6, line_px=2):
    """Перспективный рендер. focus_box — доли габарита [x0,y0,z0,x1,y1,z1] для крупного плана."""
    W, H = size[0] * ss, size[1] * ss
    lo, hi = model.bbox()
    if focus_box:
        fb = np.array(focus_box, float)
        flo, fhi = lo + (hi - lo) * fb[:3], lo + (hi - lo) * fb[3:]
    else:
        flo, fhi = lo, hi
    target = (flo + fhi) / 2
    diag = np.linalg.norm(hi - lo)
    cam, r, u, f = camera_basis(target, az, el, diag * dist_factor)

    # грани
    faces = []
    for pi, p in enumerate(model.parts):
        for verts, n in p.faces():
            V = np.array(verts, float)
            c = V.mean(0)
            if np.dot(np.array(n, float), cam - c) <= 0:
                continue
            faces.append((pi, V, np.array(n, float)))
    allpts = np.vstack([p.corners() for p in model.parts])
    fitpts = np.array([[x, y, z] for x in (flo[0], fhi[0]) for y in (flo[1], fhi[1]) for z in (flo[2], fhi[2])])
    sp_fit, _ = project_persp(fitpts, cam, r, u, f)
    smin, smax = sp_fit.min(0), sp_fit.max(0)
    scale = min(W * fill / (smax[0] - smin[0]), H * fill / (smax[1] - smin[1]))
    ctr = (smin + smax) / 2

    def to_px(sp):
        return np.stack([(sp[:, 0] - ctr[0]) * scale + W / 2, H / 2 - (sp[:, 1] - ctr[1]) * scale], 1)

    tris, shade = [], []
    for fid, (pi, V, n) in enumerate(faces):
        sp, z = project_persp(V, cam, r, u, f)
        P = to_px(sp)
        tris.append((P[[0, 1, 2]], z[[0, 1, 2]], fid))
        tris.append((P[[0, 2, 3]], z[[0, 2, 3]], fid))
        k = 0.58 + 0.42 * max(0.0, float(np.dot(n, LIGHT)))
        if n[2] > 0.5:
            k = max(k, 0.95)
        col = np.array(model.parts[pi].color, float) * k
        shade.append(np.clip(col, 0, 255))
    idbuf, _ = _raster(tris, W, H)

    # фон + свечение
    bg = np.full((H, W, 3), 255.0)
    for g in model.glows:
        Vg = np.array([[g.x0, g.y0, 1], [g.x1, g.y0, 1], [g.x1, g.y1, 1], [g.x0, g.y1, 1]], float)
        sp, _ = project_persp(Vg, cam, r, u, f)
        P = to_px(sp)
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon([tuple(p) for p in P], fill=255)
        depth = float(np.mean((Vg - cam) @ f))
        blur_px = float(g.blur_mm * scale / max(1.0, depth))
        m = m.filter(ImageFilter.GaussianBlur(max(4.0, blur_px)))
        a = np.array(m, float)[..., None] / 255.0
        bg = bg * (1 - a * 0.85) + np.array(g.color, float) * a * 0.85
    # контактная тень на полу (мягкая)
    floor_parts = [p for p in model.parts if p.z0 <= 1]
    if floor_parts:
        m = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(m)
        for p in floor_parts:
            Vf = np.array([[p.x0, p.y0, 0], [p.x1, p.y0, 0], [p.x1, p.y1, 0], [p.x0, p.y1, 0]], float)
            sp, _ = project_persp(Vf, cam, r, u, f)
            d.polygon([tuple(q) for q in to_px(sp)], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(14 * ss))
        a = np.array(m, float)[..., None] / 255.0
        bg = bg * (1 - a * 0.22)

    img = bg.copy()
    mask = idbuf >= 0
    shade_arr = np.array(shade) if shade else np.zeros((1, 3))
    img[mask] = shade_arr[idbuf[mask]]
    edges = _edges(idbuf, thickness=line_px * ss // 1)
    clay = img.copy()
    clay[edges] = clay[edges] * 0.35
    line = np.full((H, W, 3), 255.0)
    line[edges] = 20

    def out(a, mode="RGB"):
        im = Image.fromarray(a.astype(np.uint8), mode)
        return im.resize(size, Image.LANCZOS)

    silhouette = Image.fromarray((mask * 255).astype(np.uint8), "L").resize(size, Image.LANCZOS)
    return {"clay": out(clay), "line": out(line), "mask": silhouette}


# ---------------------------------------------------------------- чертёж с размерами

def _font(px):
    return ImageFont.truetype(FONT_PATH, px)


def _dim(draw, a, b, offset, text, font, horizontal=True, color=(30, 30, 30)):
    """Размерная линия между точками a,b (px) со сдвигом offset."""
    (ax, ay), (bx, by) = a, b
    if horizontal:
        y = ay + offset
        draw.line([(ax, ay), (ax, y + (6 if offset > 0 else -6))], fill=(150, 150, 150), width=1)
        draw.line([(bx, by), (bx, y + (6 if offset > 0 else -6))], fill=(150, 150, 150), width=1)
        draw.line([(ax, y), (bx, y)], fill=color, width=2)
        for x, s in ((ax, 1), (bx, -1)):
            draw.polygon([(x, y), (x + 10 * s, y - 4), (x + 10 * s, y + 4)], fill=color)
        tw = draw.textlength(text, font=font)
        draw.rectangle([((ax + bx) / 2 - tw / 2 - 4, y - font.size - 4), ((ax + bx) / 2 + tw / 2 + 4, y - 2)], fill="white")
        draw.text(((ax + bx) / 2 - tw / 2, y - font.size - 4), text, fill=color, font=font)
    else:
        x = ax + offset
        draw.line([(ax, ay), (x + (6 if offset > 0 else -6), ay)], fill=(150, 150, 150), width=1)
        draw.line([(bx, by), (x + (6 if offset > 0 else -6), by)], fill=(150, 150, 150), width=1)
        draw.line([(x, ay), (x, by)], fill=color, width=2)
        for y, s in ((ay, 1), (by, -1)):
            draw.polygon([(x, y), (x - 4, y + 10 * s), (x + 4, y + 10 * s)], fill=color)
        txt = Image.new("L", (int(draw.textlength(text, font=font)) + 8, font.size + 8), 0)
        ImageDraw.Draw(txt).text((4, 2), text, fill=255, font=font)
        txt = txt.rotate(90, expand=True)
        return (txt, (int(x - txt.size[0] - 4), int((ay + by) / 2 - txt.size[1] / 2)))
    return None


def ortho_view(model: Model, view, px_per_mm, origin, canvas: Image.Image):
    """Рисует один вид на холсте; возвращает функцию мм->px для размеров."""
    W, H = canvas.size
    faces = []
    for pi, p in enumerate(model.parts):
        for verts, n in p.faces():
            faces.append((pi, np.array(verts, float), np.array(n, float)))
    tris = []
    ox, oy = origin

    def to_px(sp):
        return np.stack([ox + sp[:, 0] * px_per_mm, oy - sp[:, 1] * px_per_mm], 1)

    vdir = {"front": np.array([0, 1, 0.]), "side": np.array([-1, 0, 0.]), "top": np.array([0, 0, -1.])}[view]
    for fid, (pi, V, n) in enumerate(faces):
        if np.dot(n, -vdir) <= 1e-9:
            continue
        sp, z = project_ortho(V, view)
        P = to_px(sp)
        tris.append((P[[0, 1, 2]], z[[0, 1, 2]], fid))
        tris.append((P[[0, 2, 3]], z[[0, 2, 3]], fid))
    idbuf, _ = _raster(tris, W, H)
    arr = np.array(canvas).astype(float)
    mask = idbuf >= 0
    fills = np.array([np.array(model.parts[pi].color, float) * 0.25 + 255 * 0.75 for pi, _, _ in faces])
    arr[mask] = fills[idbuf[mask]]
    e = _edges(idbuf, 2)
    arr[e] = 25
    canvas.paste(Image.fromarray(arr.astype(np.uint8)))

    def mm(p2):
        return (ox + p2[0] * px_per_mm, oy - p2[1] * px_per_mm)
    return mm


def scheme(model: Model, title: str, size=(1600, 1250)):
    """Три вида (спереди, сбоку, сверху) с габаритными размерами."""
    lo, hi = model.bbox()
    Wmm, Dmm, Hmm = hi - lo
    canvas = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(canvas)
    f_title, f_dim, f_lbl = _font(30), _font(22), _font(20)
    draw.text((40, 28), title, fill=(20, 20, 20), font=f_title)
    # раскладка: спереди слева сверху, сбоку справа сверху, сверху под видом спереди
    margin, gap = 110, 140
    avail_w = size[0] - 2 * margin - gap
    avail_h = size[1] - 120 - 2 * margin - gap
    k = min(avail_w / (Wmm + Dmm), avail_h / (Hmm + Dmm))
    fx0, fy0 = margin + 40, 120 + margin + Hmm * k
    sx0 = fx0 + Wmm * k + gap
    ty0 = fy0 + gap + 30 + Dmm * k
    rotated = []

    shift = lambda pts, axes: pts  # noqa: E731
    # смещаем модель в 0
    m0 = Model(parts=[Part(p.name, p.x0 - lo[0], p.y0 - lo[1], p.z0 - lo[2], p.x1 - lo[0], p.y1 - lo[1],
                           p.z1 - lo[2], p.color, p.group) for p in model.parts], dims=model.dims)
    ortho_view(m0, "front", k, (fx0, fy0), canvas)
    ortho_view(m0, "side", k, (sx0, fy0), canvas)
    ortho_view(m0, "top", k, (fx0, ty0), canvas)
    draw = ImageDraw.Draw(canvas)
    for (x, y, t) in ((fx0, fy0 + 64, "Вид спереди"), (sx0, fy0 + 64, "Вид сбоку"),
                      (fx0, ty0 + 14, "Вид сверху")):
        draw.text((x, y), t, fill=(110, 110, 110), font=f_lbl)
    _dim(draw, (fx0, fy0), (fx0 + Wmm * k, fy0), 46, f"{Wmm:.0f}", f_dim)
    r = _dim(draw, (fx0, fy0), (fx0, fy0 - Hmm * k), -50, f"{Hmm:.0f}", f_dim, horizontal=False)
    if r:
        rotated.append(r)
    _dim(draw, (sx0, fy0), (sx0 + Dmm * k, fy0), 46, f"{Dmm:.0f}", f_dim)
    for d in model.dims:  # (view, axis, a_mm, b_mm, at_mm, offset_px, text)
        view, axis, a, b, at, off, text = d
        if view == "front" and axis == "x":
            _dim(draw, (fx0 + (a - lo[0]) * k, fy0 - (at - lo[2]) * k), (fx0 + (b - lo[0]) * k, fy0 - (at - lo[2]) * k), off, text, f_dim)
        if view == "front" and axis == "z":
            rr = _dim(draw, (fx0 + (at - lo[0]) * k, fy0 - (a - lo[2]) * k), (fx0 + (at - lo[0]) * k, fy0 - (b - lo[2]) * k), off, text, f_dim, horizontal=False)
            if rr:
                rotated.append(rr)
        if view == "side" and axis == "y":
            _dim(draw, (sx0 + (a - lo[1]) * k, fy0 - (at - lo[2]) * k), (sx0 + (b - lo[1]) * k, fy0 - (at - lo[2]) * k), off, text, f_dim)
        if view == "side" and axis == "z":
            rr = _dim(draw, (sx0 + (at - lo[1]) * k, fy0 - (a - lo[2]) * k), (sx0 + (at - lo[1]) * k, fy0 - (b - lo[2]) * k), off, text, f_dim, horizontal=False)
            if rr:
                rotated.append(rr)
    for im, pos in rotated:
        black = Image.new("RGB", im.size, (30, 30, 30))
        canvas.paste(black, pos, im)
    draw.text((40, 72), "Размеры в мм. Схема для сайта и согласования; производственный чертёж — конструктор Arvello.",
              fill=(120, 120, 120), font=f_lbl)
    return canvas
