import pygame
import time
import math

# Initialize pygame
pygame.init()
# Initialize fonts
pygame.font.init()

from utils import scale_image, blit_rotate_center

# Load images
GRASS = scale_image(pygame.image.load('imgs/grass.jpg'), 2.5)
TRACK = scale_image(pygame.image.load('imgs/track.png'), 0.9)
TRACK_BORDER = scale_image(pygame.image.load('imgs/track-border.png'), 0.9)
FINISH = pygame.image.load('imgs/finish.png')
FINISH_MASK = pygame.mask.from_surface(FINISH) # for detecting collisions with the finish line
FINISH_POSITION = (110, 240) # stores the X and Y coordinates of the finish line

RED_CAR = scale_image(pygame.image.load('imgs/red-car.tif'), 0.4)
BLUE_CAR = scale_image(pygame.image.load('imgs/blue-car.tif'), 0.4)

# game window size
WIN_WIDTH, WIN_HEIGHT = 700, 630
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Car Racing")

# Scale track and border
TRACK = pygame.transform.scale(TRACK, (WIN_WIDTH, WIN_HEIGHT))
TRACK_BORDER = pygame.transform.scale(TRACK_BORDER, (WIN_WIDTH, WIN_HEIGHT))
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)

# game fps
FPS = 60

# Define controls for both players
PLAYER_CONTROLS = {
    "player1": {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "up": pygame.K_UP, "down": pygame.K_DOWN},
    "player2": {"left": pygame.K_a, "right": pygame.K_d, "up": pygame.K_w, "down": pygame.K_s},
}

# Base Car Class
class AbstractCar:
    def __init__(self, max_velocity, rotation_velocity):
        self.img = self.IMG # stores the cars image
        self.max_velocity = max_velocity # top speed of the car
        self.velocity = 0
        self.rotation_velocity = rotation_velocity # how much the car rotates per move
        self.angle = 0 # the direction the car is facing
        self.x, self.y = self.START_POS # sets the starting position of the car
        self.acceleration = 0.1 # controls how quickly the car speeds up
        self.finish_time = None  # stores when the car crosses the finish line
        self.speed = 0

    # rotating the car
    def rotate(self, left=False, right=False):
        if left:
            self.angle += self.rotation_velocity
        elif right:
            self.angle -= self.rotation_velocity

    # drawing the car
    def draw(self, win):
        blit_rotate_center(WIN, self.img, (self.x, self.y), self.angle)

    # moving the car forward
    def move_forward(self):
        # increases the speed by the acceleration, but doesn't let it go past the maximum speed
        self.velocity = min(self.velocity + self.acceleration, self.max_velocity)
        self.move()

    # moving the car backward
    def move_backward(self):
        # reduces the speed by the acceleration, but doesn’t let it go lower than half of the max speed in reverse
        self.velocity = max(self.velocity - self.acceleration, -self.max_velocity / 2)
        self.move()

    # updates the cars position
    def move(self):
        radians = math.radians(self.angle) # converting degrees to radians
        vertical = math.cos(radians) * self.velocity # calculates vertical movement
        horizontal = math.sin(radians) * self.velocity # calculates horizontal movement
        # update the cars position
        self.y -= vertical
        self.x -= horizontal

    # checks for collisions between car and object
    def collide(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.img) # used to check for collisions
        offset = (int(self.x - x), int(self.y - y)) # calculates the difference in position between the two objects
        poi = mask.overlap(car_mask, offset) # calculates point of impact
        return poi

    # checks for collisions between cars
    def check_collision(self, other_car):
        # Create masks for accurate pixel-perfect collision detection
        self_mask = pygame.mask.from_surface(self.img)
        other_mask = pygame.mask.from_surface(other_car.img)

        # Calculate the difference in position between the two cars
        offset = (int(other_car.x - self.x), int(other_car.y - self.y))
        collision_point = self_mask.overlap(other_mask, offset)  # Gets collision point

        if collision_point:
            # Head-on collision (cars moving towards each other)
            if (self.velocity > 0 and other_car.velocity < 0) or (self.velocity < 0 and other_car.velocity > 0):
                self.velocity *= -0.5
                other_car.velocity *= -0.5
            # Rear-end collision (one car hits another from behind)
            else:
                self.velocity, other_car.velocity = other_car.velocity, self.velocity

            self.move()
            other_car.move()

    # resets the car
    def reset(self):
        self.x, self.y = self.START_POS # moves the car back to the starting position
        # resets its angle, speed, and finish time
        self.angle = 0
        self.velocity = 0
        self.finish_time = None

    # slows down the car
    def reduce_speed(self):
        # ensures that speed never goes below 0
        self.velocity = max(self.velocity - self.acceleration, 0)
        # if the car still has speed, it keeps moving
        if self.velocity > 0:
            self.move()

    # bounces the car after collision
    def bounce(self):
        self.velocity *= -0.5 # the speed becomes negative and is cut in half
        self.move() # updates the object's position based on the new velocity

# Player Cars
class PlayerCar1(AbstractCar):
    IMG = RED_CAR
    START_POS = (145, 200)

class PlayerCar2(AbstractCar):
    IMG = BLUE_CAR
    START_POS = (118, 200)

# Function to move a player based on key input
def move_player(car, controls):
    keys = pygame.key.get_pressed() # detects which keys are pressed
    moved = False # tracks whether the car is moving

    if keys[controls["left"]]:
        car.rotate(left=True)
    if keys[controls["right"]]:
        car.rotate(right=True)
    if keys[controls["up"]]:
        moved = True
        car.move_forward()
    if keys[controls["down"]]:
        moved = True
        car.move_backward()

    if not moved:
        car.reduce_speed()

race_start_time = None

# checks if a car has crossed the finish line
def check_finish(car, FINISH_MASK, FINISH_POSITION, race_start_time, player_car1, player_car2):
    # if the car has already finished, do nothing
    if car.finish_time is not None:
        return False

    # checks if the car collides with the finish line
    finish_poi_collide = car.collide(FINISH_MASK, *FINISH_POSITION)

    if finish_poi_collide is not None:
        finish_y = finish_poi_collide[1] # the Y position where the car hit the finish line
        finish_height = FINISH_MASK.get_size()[1] # the total height of the finish line

        # if the car hits the top of the finish line, it bounces back
        if finish_y <= 5:
            car.bounce()
        # if the car hits the bottom of the finish line while moving forward, it has finished the race
        elif finish_y >= finish_height - 5:
            if car.velocity > 0:
                car.finish_time = time.time() - race_start_time # time the car took to reach the finish line
                # declares the winner
                if isinstance(car, PlayerCar1):
                    declare_winner(car, "RED CAR (PLAYER 1)", car.finish_time)
                    return True
                else:
                    declare_winner(car, "BLUE CAR (PLAYER 2)", car.finish_time)
                    return True
            # if the car isn’t moving forward, it bounces back instead of finishing
            else:
                car.bounce()

# declares the winner
def declare_winner(car, car_name, finish_time):
    FONT = pygame.font.Font(None, 25)  # Choose font & size

    # creates a popup window
    popup_width, popup_height = 300, 150
    popup = pygame.Surface((popup_width, popup_height))
    popup.fill((0, 0, 0))  # Black background

    # converts the winner’s name and finish time into text images
    text = FONT.render(f"{car_name} WINS!", True, (255, 255, 255))
    time_text = FONT.render(f"Time: {finish_time:.2f}s", True, (255, 255, 255))

    # centers the text inside the popup
    text_rect = text.get_rect(center=(popup_width // 2, 40))
    time_rect = time_text.get_rect(center=(popup_width // 2, 90))

    # adds the text to the popup
    popup.blit(text, text_rect)
    popup.blit(time_text, time_rect)

    # positions the popup in the center of the main window
    popup_x = (WIN.get_width() - popup_width) // 2
    popup_y = (WIN.get_height() - popup_height) // 2

    # draws the popup onto the main game window
    WIN.blit(popup, (popup_x, popup_y))
    pygame.display.update()

    pygame.time.delay(2000)  # pauses for 2 seconds before resetting
    car.reset()
    return True

# function that displays the speed of each car on the screen
def draw_speed(win, car, x, y):
    FONT_SPEED = pygame.font.Font(None, 30)
    text_color = (255, 0, 0) if car == player_car1 else (0, 0, 255)

    speed_text = FONT_SPEED.render(f"Speed: {abs(int(car.velocity))} px/s", True, text_color)

    # gets text size
    text_width, text_height = speed_text.get_width(), speed_text.get_height()

    # draws black rectangle behind text
    padding = 5  # Extra padding around the text
    pygame.draw.rect(win, (0, 0, 0), (x - padding, y - padding, text_width + 2 * padding, text_height + 2 * padding))

    # draws text on top of rectangle
    win.blit(speed_text, (x, y))

#  function that displays the elapsed time on the screen
def draw_timer(win, x, y):
    """Displays the elapsed time since the race started."""
    FONT_TIME = pygame.font.Font(None, 30)

    if race_start_time is not None:
        elapsed_time = int(time.time() - race_start_time)  # Calculate elapsed time in seconds
        time_text = FONT_TIME.render(f"Time: {elapsed_time}s", True, (255, 165, 0))

        # gets text size
        text_width, text_height = time_text.get_width(), time_text.get_height()

        # draws black rectangle behind text
        padding = 5  # Extra padding around the text
        pygame.draw.rect(win, (0, 0, 0),(x - padding, y - padding, text_width + 2 * padding, text_height + 2 * padding))

        win.blit(time_text, (x, y))  # Draw the timer on screen at (x, y)

# Function to draw the game
def draw(win, images, cars):
    for img, pos in images:
        win.blit(img, pos)

    for car in cars:
        car.draw(win)

    for light in traffic_lights:
        light.draw(WIN)

    # Draw speed indicators
    draw_speed(win, player_car1, 7, 550)
    draw_speed(win, player_car2, 7, 580)

    draw_timer(WIN, 7, 520)

    pygame.display.update()

class TrafficLight:
    def __init__(self, red_img, yellow_img, green_img, position):
        scale_size = (20, 40)

        # loads each image from the file and stores them in a dictionary
        self.images = {
            "red": pygame.transform.scale(pygame.image.load(red_img), scale_size),
            "yellow": pygame.transform.scale(pygame.image.load(yellow_img), scale_size),
            "green": pygame.transform.scale(pygame.image.load(green_img), scale_size)
        }
        self.position = position # stores the location of the traffic light on the screen
        self.state = "red"
        self.last_change_time = time.time() # stores the exact time when the light last changed

    def draw(self, win):
        win.blit(self.images[self.state], self.position)

    def update(self):
        elapsed_time = time.time() - self.last_change_time
        if self.state == "red" and elapsed_time > 3:
            self.state = "yellow"
            self.last_change_time = time.time()
        elif self.state == "yellow" and elapsed_time > 1.5:
            self.state = "green"
            self.last_change_time = time.time()

    def is_green(self):
        return self.state == "green"

    def reset(self):
        # resets the traffic light to red and restarts the timer
        self.state = "red"
        self.last_change_time = time.time()

traffic_lights = [
    TrafficLight("imgs/red.png", "imgs/orange.png", "imgs/green.png", (10, 10)),  # First light
    TrafficLight("imgs/red.png", "imgs/orange.png", "imgs/green.png", (40, 10)),  # Second light (next to the first)
    TrafficLight("imgs/red.png", "imgs/orange.png", "imgs/green.png", (70, 10))  # Third light (next to the second)
]

# Game Loop
run = True
clock = pygame.time.Clock() # controls the frame rate of the game
images = [(GRASS, (0, 0)), (TRACK, (0, 0)), (FINISH, FINISH_POSITION), (TRACK_BORDER, (0, 0))]

# creates the player cars
player_car1 = PlayerCar1(4, 4)
player_car2 = PlayerCar2(4, 4)

# groups the cars into a list
cars = [player_car1, player_car2]

while run:
    clock.tick(FPS) # limits the speed of the loop to avoid super-fast execution

    draw_speed(WIN, player_car1, 7, 550)  # Speed for Player 1 (top-left)
    draw_speed(WIN, player_car2, 7, 580)  # Speed for Player 2 (below Player 1 speed)

    # handles events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    # updates the traffic lights
    for light in traffic_lights:
        light.update()

    # Start timer when the first light turns green
    if race_start_time is None and traffic_lights[0].is_green():
        race_start_time = time.time()

    # allows movement only if the light is green
    if all(light.is_green() for light in traffic_lights):
        move_player(player_car1, PLAYER_CONTROLS["player1"])
        move_player(player_car2, PLAYER_CONTROLS["player2"])

    # handles car collisions
    if player_car1.check_collision(player_car2):
        player_car1.bounce()
        player_car2.bounce()

    finished = False

    # checks for track collisions and finishing line
    for car in cars:
        if car.collide(TRACK_BORDER_MASK) is not None:
            car.bounce()

        if check_finish(car, FINISH_MASK, FINISH_POSITION, race_start_time, player_car1, player_car2):
            finished = True

    # restarts the race if someone finishes
    if finished:  # If a player wins
        pygame.time.delay(3000)  # Show winner popup
        race_start_time = None
        #race_start_time = time.time()  # Restart timer
        player_car1.reset()
        player_car2.reset()
        for light in traffic_lights:  # reset all traffic lights
            light.reset()

    # redraws the entire game
    draw(WIN, images, cars)

pygame.quit()

