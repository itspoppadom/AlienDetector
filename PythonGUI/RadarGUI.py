# RGU Hackathon 2025 - RGU Engineering Challenge
# Authors - Circuit Breakers - RH, DC, OR, MT, JS
import pygame
from pygame.locals import *
import math
import json
import serial
import time

# Initialize pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 480, 700
# Change back to 320 in order to fit the screen of the 3.5 inch RPi Screen
# Height of the window is increased to 700 to stretch the window in portrait mode on 3.5 inch RPi Screen
# Add pygame.NOFRAME to remove the window frame/ Remove pygame.NOFRAME to display the window frame
window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Real-Time Radar")

# Define colors
BLACK = (0, 0, 0)
NEON_GREEN = (57, 255, 20)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# Radar Center & Radius
center_x, center_y = 240, 280
radius = 230

pulse_speed = 3  # Speed of pulse expansion

# List to store expanding pulses
pulses = []

# Connect to Arduino Nano
SERIAL_PORT = "COM8"  # Change for Linux: "/dev/ttyUSB0" or "/dev/ttyACM0" depending on your system
BAUD_RATE = 115200
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except serial.SerialException:
    print("Error: Could not open serial port")
    ser = None

# Object Storage
detected_objects = []

# Function to draw vertical battery icon (top-right) with 2/3 charge
def draw_battery():
    x, y = WIDTH - 30, 20  
    pygame.draw.rect(window, WHITE, (x, y, 15, 30), 2)  # Battery outline
    pygame.draw.rect(window, WHITE, (x + 4, y - 5, 7, 5))  # Battery tip

    # 2/3 full battery (two large green bars)
    pygame.draw.rect(window, NEON_GREEN, (x + 3, y + 4, 9, 9))   # First large bar
    pygame.draw.rect(window, NEON_GREEN, (x + 3, y + 16, 9, 9))  # Second large bar

# Initialize font
pygame.font.init()
font = pygame.font.SysFont('Arial', 12)

def draw_radar_background():
    """ Draws the static radar elements (arc & center circle). """
    window.fill(BLACK)
    pygame.draw.arc(window, NEON_GREEN, (center_x - radius, center_y - radius, 2 * radius, 2 * radius), 
                    math.radians(0), math.radians(180), 2)
    pygame.draw.circle(window, NEON_GREEN, (center_x, center_y), 15, 2)
    
    # Draw smaller arcs with breaking line effect
    draw_broken_arc(center_x, center_y, radius * 0.66, 0, 180, NEON_GREEN, 2)
    draw_broken_arc(center_x, center_y, radius * 0.33, 0, 180, NEON_GREEN, 2)
    
    pygame.draw.line(window, NEON_GREEN, (center_x, center_y - radius), (center_x, center_y + radius), 2)
    pygame.draw.line(window, NEON_GREEN, (center_x - radius, center_y), (center_x + radius, center_y), 2)

    # Draw distance markers
    draw_distance_marker(center_x - 60 , center_y - 5, "0.5m")
    draw_distance_marker(center_x -140, center_y - 5 , "1.0m")
    draw_distance_marker(center_x -210, center_y - 5 , "1.5m")

def draw_broken_arc(center_x, center_y, radius, start_angle, end_angle, color, width, dash_length=10):
    """ Draws a broken arc with specified dash length. """
    angle_step = dash_length / radius
    for angle in range(start_angle, end_angle, int(math.degrees(angle_step) * 2)):
        start_rad = math.radians(angle)
        end_rad = math.radians(angle + math.degrees(angle_step))
        pygame.draw.arc(window, color, (center_x - radius, center_y - radius, 2 * radius, 2 * radius), 
                        start_rad, end_rad, width)

def draw_distance_marker(x, y, text):
    """ Draws a distance marker at the specified position. """
    text_surface = font.render(text, True, NEON_GREEN)
    window.blit(text_surface, (x - text_surface.get_width() // 2, y - text_surface.get_height() // 2))

def draw_objects():
    """ Draws all detected objects from stored data. """
    current_time = time.time()
    for obj in detected_objects:
        # Check if the object has expired (e.g., 5 seconds)
        if current_time - obj["timestamp"] < 5:
#Distance obtained by the sensor needs to be multiplied by the difference between the radius of radar and the max distance set out in the firmware
            distnace = obj["distance"]
            angle = obj["angle"]             
            draw_point(distance *1.5, angle)
        else:
            detected_objects.remove(obj)

def draw_point(distance, angle):
    """ Draws a detected object at the given distance and angle. """
    angle_rad = math.radians(angle)
    x = center_x + distance * math.cos(angle_rad)
    y = center_y - distance * math.sin(angle_rad)
    pygame.draw.circle(window, RED, (int(x), int(y)), 5)

def read_sensor_data():
    """ Reads and processes incoming sensor data from serial. """
    if ser and ser.in_waiting > 0:
        try:
            raw_data = ser.readline().decode("utf-8").strip()
            print(f"Raw data: {raw_data}")  # Debugging statement
            json_data = json.loads(raw_data)
            print(f"JSON data: {json_data}")  # Debugging statement

            if "amount" in json_data and "arr" in json_data:
                return json_data["arr"]

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error: Invalid JSON received - {e}")
    return []

# Main Loop
running = True
pulse_timer = 0  # Timer to control pulse generation
pulse_interval = 500  # Interval in milliseconds to generate new pulses

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    # Read sensor data
    sensor_data = read_sensor_data()

    for data in sensor_data:
        distance = data.get("distance")
        angle = data.get("degree")
        if distance is not None and angle is not None:
            detected_objects.append({"angle": angle, "distance": distance, "timestamp": time.time()})

    # Update display
    draw_radar_background()
    draw_objects()
    draw_battery()

    # Generate new pulse at regular intervals
    current_time = pygame.time.get_ticks()
    if current_time - pulse_timer > pulse_interval:
        pulses.append(0)  # Add a new pulse with initial radius 0
        pulse_timer = current_time

    # Update and draw expanding circles
    for i in range(len(pulses)):
        pulses[i] += pulse_speed  # Increase radius

        # Adjust alpha based on size for fading effect
        alpha = max(255 - int((pulses[i] / radius) * 255), 50)  # Fade out gradually
        pulse_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(pulse_surface, (57, 255, 20, alpha), (center_x, center_y), pulses[i], 2)
        window.blit(pulse_surface, (0, 0))

    # Remove circles that exceed the radar range
    pulses = [p for p in pulses if p < radius]

    # Draw a black rectangle to hide the lower half of the pulses
    pygame.draw.rect(window, BLACK, (0, center_y, WIDTH, HEIGHT - center_y))

    pygame.display.update()
    pygame.time.delay(50)  # Control sweep speed

pygame.quit()
if ser:
    ser.close()