import pygame
import sys
import math

pygame.init()

# Screen
WIDTH, HEIGHT = 900, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Clean Respiratory Model - CGIP Final")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28, bold=True)

# Colors
BLACK = (5, 5, 5)
LUNG_COLOR = (225, 120, 110)
BRONCHI_COLOR = (70, 20, 15)
TRACHEA_COLOR = (220, 230, 245)
RING_COLOR = (180, 200, 220)
DIAPHRAGM_COLOR = (110, 35, 35)
WHITE = (255, 255, 255)

time_value = 0


# ---------------------------------------------------------
# DDA LINE DRAWING ALGORITHM
# ---------------------------------------------------------
def draw_line_dda(surface, color, x1, y1, x2, y2, thickness=1):

    dx = x2 - x1
    dy = y2 - y1

    steps = int(max(abs(dx), abs(dy)))

    if steps == 0:
        return

    x_inc = dx / steps
    y_inc = dy / steps

    x = x1
    y = y1

    for i in range(steps):
        surface.fill(color, (int(x), int(y), thickness, thickness))
        x += x_inc
        y += y_inc


# ---------------------------------------------------------
# MIDPOINT CIRCLE ALGORITHM (TRACHEA RINGS)
# ---------------------------------------------------------
def draw_ring(surface, color, center, radius, thickness=1):

    cx, cy = center
    x = 0
    y = radius
    p = 1 - radius

    vertical_scale = 0.35

    def plot_points(px, py):

        scaled_py = int(py * vertical_scale)
        scaled_px = int(px * vertical_scale)

        points = [
            (cx + px, cy + scaled_py),
            (cx - px, cy + scaled_py),
            (cx + px, cy - scaled_py),
            (cx - px, cy - scaled_py),
            (cx + py, cy + scaled_px),
            (cx - py, cy + scaled_px),
            (cx + py, cy - scaled_px),
            (cx - py, cy - scaled_px),
        ]

        for point in points:
            if 0 <= point[0] < surface.get_width() and 0 <= point[1] < surface.get_height():
                surface.fill(color, (point[0], point[1], thickness, thickness))

    plot_points(x, y)

    while x < y:

        x += 1

        if p < 0:
            p += 2 * x + 1
        else:
            y -= 1
            p += 2 * (x - y) + 1

        plot_points(x, y)


# ---------------------------------------------------------
# LUNG SHAPE
# ---------------------------------------------------------
def get_refined_lungs(scale):

    cx, cy = WIDTH // 2, HEIGHT // 2 - 30
    gap = 35

    right_pts = [
        (cx + gap + 5, cy - 230 * scale),
        (cx + gap + 100 * scale, cy - 180 * scale),
        (cx + gap + 160 * scale, cy + 50 * scale),
        (cx + gap + 145 * scale, cy + 240 * scale),
        (cx + gap + 25 * scale, cy + 180 * scale),
        (cx + gap + 5, cy + 150 * scale),
    ]

    left_pts = [
        (cx - gap - 5, cy - 230 * scale),
        (cx - gap - 80 * scale, cy - 180 * scale),
        (cx - gap - 140 * scale, cy + 30 * scale),
        (cx - gap - 130 * scale, cy + 240 * scale),
        (cx - gap - 45 * scale, cy + 180 * scale),
        (cx - gap - 5, cy + 160 * scale),
    ]

    return left_pts, right_pts


# ---------------------------------------------------------
# RESPIRATORY TREE
# ---------------------------------------------------------
def draw_respiratory_tree(scale):

    cx = WIDTH // 2
    t_top = 80
    t_h = 210
    t_w = 36
    t_bottom = t_top + t_h

    # Trachea
    pygame.draw.rect(screen, TRACHEA_COLOR,
                     (cx - t_w // 2, t_top, t_w, t_h),
                     border_radius=4)

    # Rings
    ring_surface = pygame.Surface((t_w, t_h), pygame.SRCALPHA)

    for i in range(11):
        local_center = (t_w // 2, i * 19 + 12)
        draw_ring(ring_surface, RING_COLOR, local_center, t_w // 2 - 4, 2)

    screen.blit(ring_surface, (cx - t_w // 2, t_top))

    gap = 35
    l_entry = (cx - gap, t_bottom + 40)
    r_entry = (cx + gap, t_bottom + 40)

    # MAIN BRONCHI (DDA)
    draw_line_dda(screen, BRONCHI_COLOR, cx, t_bottom, l_entry[0], l_entry[1], 6)
    draw_line_dda(screen, BRONCHI_COLOR, cx, t_bottom, r_entry[0], r_entry[1], 6)

    # LUNG MASK
    l_pts, r_pts = get_refined_lungs(scale)

    mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), l_pts)
    pygame.draw.polygon(mask, (255, 255, 255, 255), r_pts)

    branch_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    for side_entry, mult in [(l_entry, -1), (r_entry, 1)]:

        stem_end = (
            side_entry[0] + 60 * mult * scale,
            side_entry[1] + 70 * scale
        )

        draw_line_dda(branch_layer, BRONCHI_COLOR,
                      side_entry[0], side_entry[1],
                      stem_end[0], stem_end[1], 4)

        for i in range(3):

            angle = math.radians(-15 + i * 40) if mult == 1 else math.radians(195 - i * 40)

            length = 80 * scale

            branch_end = (
                stem_end[0] + math.cos(angle) * length,
                stem_end[1] + math.sin(angle) * length
            )

            draw_line_dda(branch_layer, BRONCHI_COLOR,
                          stem_end[0], stem_end[1],
                          branch_end[0], branch_end[1], 2)

    branch_layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    screen.blit(branch_layer, (0, 0))


# ---------------------------------------------------------
# DIAPHRAGM
# ---------------------------------------------------------
def draw_diaphragm(inhale):

    cx = WIDTH // 2

    base_y = 660 + (50 * inhale)
    dome_height = 85 - (40 * inhale)

    pts = []

    for x in range(cx - 380, cx + 381, 10):

        dist = (x - cx) / 380
        curve = (1 - dist ** 2) * dome_height

        pts.append((x, base_y - curve))

    pygame.draw.polygon(screen, DIAPHRAGM_COLOR,
                        [(cx - 380, HEIGHT)] +
                        pts +
                        [(cx + 380, HEIGHT)])

    pygame.draw.lines(screen, (160, 60, 60), False, pts, 4)


# ---------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------
running = True

while running:

    clock.tick(60)
    time_value += 0.035

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    inhale = math.sin(time_value)

    scale = 1.0 + 0.10 * inhale

    draw_diaphragm(inhale)

    l_pts, r_pts = get_refined_lungs(scale)

    pygame.draw.polygon(screen, LUNG_COLOR, l_pts)
    pygame.draw.polygon(screen, LUNG_COLOR, r_pts)

    pygame.draw.polygon(screen, (160, 70, 60), l_pts, 3)
    pygame.draw.polygon(screen, (160, 70, 60), r_pts, 3)

    draw_respiratory_tree(scale)

    msg = "INHALATION" if inhale > 0 else "EXHALATION"

    lbl = font.render(msg, True, WHITE)

    screen.blit(lbl, (WIDTH // 2 - lbl.get_width() // 2, 30))

    pygame.display.flip()

pygame.quit()
sys.exit()
