import pygame

# resizes an image
def scale_image(img, factor):
    size = round(img.get_width() * factor), round(img.get_height() * factor)
    return pygame.transform.scale(img, size)

# rotates an image around its center
def blit_rotate_center(win, image, top_left, angle):
    # creates a rotated version of the image
    rotated_image = pygame.transform.rotate(image, angle)

    # ensures that after rotation, the image stays centered at the same place instead of shifting around
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=top_left).center)

    # the rotated image is drawn (blitted) onto the screen at the adjusted position
    win.blit(rotated_image, new_rect.topleft)
