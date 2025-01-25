#!/usr/bin/env python3
# Version V2.0

import logging
import math
import pathlib
import sys
import threading
import time
import subprocess
import os
import json
from datetime import datetime
import signal

import ltr559
import lgpio as GPIO  # Change the import to lgpio
import ST7735
import yaml
from fonts.ttf import RobotoMedium as UserFont
from PIL import Image, ImageDraw, ImageFont

from grow import Piezo
from lgpio_moisture import Moisture  # Use our patched moisture module instead
from lgpio_pump import Pump  # Use our patched pump module
from chilli_screensaver import draw_chilli_animation
from threading import Thread
from threading import Event
from threading import Lock

# Global variables
viewcontroller = None
display = None
screensaver_thread = None
screensaver_stop_event = Event()
screensaver_active = False
last_button_press = 0
icons = None

# Global icon variables
icon_drop = None
icon_nodrop = None
icon_rightarrow = None
icon_alarm = None
icon_snooze = None
icon_help = None
icon_settings = None
icon_channel = None
icon_backdrop = None
icon_return = None
icon_chilli = None

FPS = 10

BUTTONS = [5, 6, 16, 24]  
LABELS = ["A", "B", "X", "Y"]

DISPLAY_WIDTH = 160
DISPLAY_HEIGHT = 80

COLOR_WHITE = (255, 255, 255)
COLOR_BLUE = (31, 137, 251)
COLOR_GREEN = (99, 255, 1)
COLOR_YELLOW = (254, 219, 82)
COLOR_RED = (247, 0, 63)
COLOR_BLACK = (0, 0, 0)

# Global lock for display access
display_lock = Lock()

def load_icons():
    """Load all required icons with error handling"""
    icon_files = {
        'drop': "icons/icon-drop.png",
        'nodrop': "icons/icon-nodrop.png",
        'rightarrow': "icons/icon-rightarrow.png",
        'alarm': "icons/icon-alarm.png",
        'snooze': "icons/icon-snooze.png",
        'help': "icons/icon-help.png",
        'settings': "icons/icon-settings.png",
        'channel': "icons/icon-channel.png",
        'backdrop': "icons/icon-backdrop.png",
        'return': "icons/icon-return.png",
        'chilli': "icons/veg-chilli.png",
    }
    icons = {}
    for name, path in icon_files.items():
        try:
            icons[name] = Image.open(path).convert("RGBA")
            logging.info(f"Loaded {path}")
        except FileNotFoundError:
            logging.error(f"Could not find icon file: {path}")
        except Exception as e:
            logging.error(f"Error loading {path}: {e}")
    return icons


class View:
    def __init__(self, image):
        self._image = image
        self._draw = ImageDraw.Draw(image)

        self.font = ImageFont.truetype(UserFont, 14)
        self.font_small = ImageFont.truetype(UserFont, 10)
    def button_a(self):
        return False

    def button_b(self):
        return False

    def button_x(self):
        return False

    def button_y(self):
        return False

    def update(self):
        pass

    def render(self):
        pass

    def clear(self):
        self._draw.rectangle((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT), (0, 0, 0))

    def icon(self, icon, position, color):
        """Draw an icon on the display at the specified position."""
        
        col = Image.new("RGBA", icon.size, color=color)
        self._image.paste(col, position, mask=icon)
        
    def label(
        self,
        position="X",
        text=None,
        bgcolor=(0, 0, 0),
        textcolor=(255, 255, 255),
        margin=4,
    ):
        if position not in ["A", "B", "X", "Y"]:
            raise ValueError(f"Invalid label position {position}")

        bbox = self._draw.textbbox((0, 0), text, font=self.font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        text_h = 11
        text_w += margin * 2
        text_h += margin * 2

        if position == "A":
            x, y = 0, 0
        if position == "B":
            x, y = 0, DISPLAY_HEIGHT - text_h
        if position == "X":
            x, y = DISPLAY_WIDTH - text_w, 0
        if position == "Y":
            x, y = DISPLAY_WIDTH - text_w, DISPLAY_HEIGHT - text_h

        x2, y2 = x + text_w, y + text_h

        self._draw.rectangle((x, y, x2, y2), bgcolor)
        self._draw.text(
            (x + margin, y + margin - 1), text, font=self.font, fill=textcolor
        )

    def overlay(self, text, top=0):
        """Draw an overlay with some auto-sized text."""
        self._draw.rectangle(
            (0, top, DISPLAY_WIDTH, DISPLAY_HEIGHT), fill=(192, 225, 254)
        )  # Overlay backdrop
        self._draw.rectangle((0, top, DISPLAY_WIDTH, top + 1), fill=COLOR_BLUE)  # Top border
        self.text_in_rect(
            text,
            self.font,
            (3, top, DISPLAY_WIDTH - 3, DISPLAY_HEIGHT - 2),
            line_spacing=1,
        )

    def text_in_rect(self, text, font, rect, line_spacing=1.1, textcolor=(0, 0, 0)):
        x1, y1, x2, y2 = rect
        width = x2 - x1
        height = y2 - y1

        # Given a rectangle, reflow and scale text to fit, centred
        while font.size > 0:
            line_height = int(font.size * line_spacing)
            max_lines = math.floor(height / line_height)
            lines = []

            # Determine if text can fit at current scale.
            words = text.split(" ")

            while len(lines) < max_lines and len(words) > 0:
                line = []

                while (
                    len(words) > 0
                    and font.getbbox(" ".join(line + [words[0]]))[2] <= width
                ):
                    line.append(words.pop(0))

                lines.append(" ".join(line))

            if len(lines) <= max_lines and len(words) == 0:
                # Solution is found, render the text.
                y = int(
                    y1
                    + (height / 2)
                    - (len(lines) * line_height / 2)
                    - (line_height - font.size) / 2
                )

                bounds = [x2, y, x1, y + len(lines) * line_height]

                for line in lines:
                    line_width = font.getbbox(line)[2]
                    x = int(x1 + (width / 2) - (line_width / 2))
                    bounds[0] = min(bounds[0], x)
                    bounds[2] = max(bounds[2], x + line_width)
                    self._draw.text((x, y), line, font=self.font, fill=textcolor)
                    y += line_height

                return tuple(bounds)

            font = ImageFont.truetype(font.path, font.size - 1)


class MainView(View):
    """Main overview.

    Displays three channels and alarm indicator/snooze.

    """

    def __init__(self, image, channels=None, alarm=None):
        self.channels = channels
        self.alarm = alarm

        View.__init__(self, image)

    def render_channel(self, channel):
        bar_x = 33
        bar_margin = 2
        bar_width = 30
        label_width = 16
        label_y = 0

        x = [
            bar_x,
            bar_x + ((bar_width + bar_margin) * 1),
            bar_x + ((bar_width + bar_margin) * 2),
        ][channel.channel - 1]

        # Saturation amounts from each sensor
        saturation = channel.sensor.saturation
        active = channel.sensor.active and channel.enabled
        warn_level = channel.warn_level

        if active:
            # Draw background bars
            self._draw.rectangle(
                (x, int((1.0 - saturation) * DISPLAY_HEIGHT), x + bar_width - 1, DISPLAY_HEIGHT),
                channel.indicator_color(saturation) if active else (229, 229, 229),
            )

        y = int((1.0 - warn_level) * DISPLAY_HEIGHT)
        self._draw.rectangle(
            (x, y, x + bar_width - 1, y), (255, 0, 0) if channel.alarm else (0, 0, 0)
        )

        # Channel selection icons
        x += (bar_width - label_width) // 2

        self.icon(icon_channel, (x, label_y), (200, 200, 200) if active else (64, 64, 64))

        # Replace number text with graphic
        bbox = self.font.getbbox(str(channel.channel))
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        self._draw.text(
            (x + int(math.ceil(8 - (tw / 2.0))), label_y + 1),
            str(channel.channel),
            font=self.font,
            fill=(55, 55, 55) if active else (100, 100, 100),
        )

    def render(self):
        self.clear()

        for channel in self.channels:
            self.render_channel(channel)

        # Icons
        self.icon(icon_backdrop, (0, 0), COLOR_WHITE)
        self.icon(icon_rightarrow, (3, 3), (55, 55, 55))

        self.alarm.render((3, DISPLAY_HEIGHT - 23))

        self.icon(icon_backdrop.rotate(180), (DISPLAY_WIDTH - 26, 0), COLOR_WHITE)
        self.icon(icon_settings, (DISPLAY_WIDTH - 19 - 3, 3), (55, 55, 55))


class EditView(View):
    """Baseclass for a settings edit view."""

    def __init__(self, image, options=[]):
        self._options = options
        self._current_option = 0
        self._change_mode = False
        self._help_mode = False
        self.channel = None

        View.__init__(self, image)

    def render(self):
        self.icon(icon_backdrop.rotate(180), (DISPLAY_WIDTH - 26, 0), COLOR_WHITE)
        self.icon(icon_return, (DISPLAY_WIDTH - 19 - 3, 3), (55, 55, 55))

        option = self._options[self._current_option]
        title = option["title"]
        prop = option["prop"]
        object = option.get("object", self.channel)
        value = getattr(object, prop)
        text = option["format"](value)
        mode = option.get("mode", "int")
        help = option["help"]

        if self._change_mode:
            self.label(
                "Y",
                "Yes" if mode == "bool" else "++",
                textcolor=COLOR_BLACK,
                bgcolor=COLOR_WHITE,
            )
            self.label(
                "B",
                "No" if mode == "bool" else "--",
                textcolor=COLOR_BLACK,
                bgcolor=COLOR_WHITE,
            )
        else:
            self.label("B", "Next", textcolor=COLOR_BLACK, bgcolor=COLOR_WHITE)
            self.label("Y", "Change", textcolor=COLOR_BLACK, bgcolor=COLOR_WHITE)

        self._draw.text((3, 36), f"{title} : {text}", font=self.font, fill=COLOR_WHITE)

        if self._help_mode:
            self.icon(icon_backdrop.rotate(90), (0, 0), COLOR_BLUE)
            self._draw.rectangle((7, 3, 23, 19), COLOR_BLACK)
            self.overlay(help, top=26)

        self.icon(icon_help, (0, 0), COLOR_BLUE)

    def button_a(self):
        self._help_mode = not self._help_mode
        return True

    def button_b(self):
        if self._help_mode:
            return True

        if self._change_mode:
            option = self._options[self._current_option]
            prop = option["prop"]
            mode = option.get("mode", "int")
            object = option.get("object", self.channel)

            value = getattr(object, prop)
            if mode == "bool":
                value = False
            else:
                inc = option["inc"]
                limit = option["min"]
                value -= inc
                if mode == "float":
                    value = round(value, option.get("round", 1))
                if value < limit:
                    value = limit
            setattr(object, prop, value)
        else:
            self._current_option += 1
            self._current_option %= len(self._options)

        return True

    def button_x(self):
        if self._change_mode:
            self._change_mode = False
            return True
        return False

    def button_y(self):
        if self._help_mode:
            return True
        if self._change_mode:
            option = self._options[self._current_option]
            prop = option["prop"]
            mode = option.get("mode", "int")
            object = option.get("object", self.channel)

            value = getattr(object, prop)
            if mode == "bool":
                value = True
            else:
                inc = option["inc"]
                limit = option["max"]
                value += inc
                if mode == "float":
                    value = round(value, option.get("round", 1))
                if value > limit:
                    value = limit
            setattr(object, prop, value)
        else:
            self._change_mode = True

        return True


class SettingsView(EditView):
    """Main settings."""

    def __init__(self, image, options=[]):
        self.main_options = options  # Store the main options
        self.screensaver_options = ["Enable Screensaver", "Disable Screensaver", "Back"]
        self.current_menu = "main"  # Track which menu we're in
        self.current_selection = 0
        super().__init__(image, options)

    def render(self):
        self.clear()
        self._draw.text(
            (28, 5),
            "Settings" if self.current_menu == "main" else "Screensaver",
            font=self.font,
            fill=COLOR_WHITE,
        )

        if self.current_menu == "main":
            # Render main settings
            option = self.main_options[self._current_option]
            title = option["title"]
            prop = option["prop"]
            object = option.get("object", self.channel)
            value = getattr(object, prop)
            text = option["format"](value)
            
            self._draw.text((3, 36), f"{title} : {text}", font=self.font, fill=COLOR_WHITE)
            
            # Add screensaver menu option at the bottom
            self._draw.text((3, 60), "Next: Screensaver Menu", font=self.font, fill=COLOR_WHITE)
        else:
            # Render screensaver menu options
            for i, option in enumerate(self.screensaver_options):
                y_position = 25 + i * 20
                color = COLOR_GREEN if i == self.current_selection else COLOR_WHITE
                self._draw.text((20, y_position), option, font=self.font, fill=color)

    def button_b(self):
        """Handle selection"""
        if self.current_menu == "main":
            return super().button_b()
        else:
            global screensaver_active, screensaver_thread, screensaver_stop_event, display, icons
            
            selected_option = self.screensaver_options[self.current_selection]
            
            if selected_option == "Enable Screensaver":
                if not screensaver_active:
                    screensaver_stop_event.clear()
                    screensaver_thread = Thread(
                        target=draw_chilli_animation,
                        args=(display, icons, screensaver_stop_event, display_lock)
                    )
                    screensaver_thread.daemon = True
                    screensaver_thread.start()
                    screensaver_active = True
                    logging.info("Screensaver enabled")
            elif selected_option == "Disable Screensaver":
                if screensaver_active:
                    screensaver_stop_event.set()
                    screensaver_active = False
                    logging.info("Screensaver disabled")
            elif selected_option == "Back":
                self.current_menu = "main"
                self.current_selection = 0
            
            return True

    def button_x(self):
        """Handle next/previous navigation"""
        if self.current_menu == "main":
            if self._current_option >= len(self.main_options) - 1:
                # Switch to screensaver menu
                self.current_menu = "screensaver"
                self.current_selection = 0
                return True
            return super().button_x()
        return True

    def button_y(self):
        """Move selection"""
        if self.current_menu == "main":
            return super().button_y()
        else:
            self.current_selection = (self.current_selection + 1) % len(self.screensaver_options)
            return True


class ScreensaverSettingsView(View):
    """Settings for configuring the screensaver."""

    def __init__(self, image):
        super().__init__(image)
        self.options = ["Enable Screensaver", "Disable Screensaver", "Back to Settings"]
        self.current_selection = 0

    def render(self):
        self.clear()
        self._draw.text(
            (20, 5),
            "Screensaver Settings",
            font=self.font,
            fill=COLOR_WHITE,
        )

        for i, option in enumerate(self.options):
            y_position = 25 + i * 20
            color = COLOR_GREEN if i == self.current_selection else COLOR_WHITE
            self._draw.text((20, y_position), option, font=self.font, fill=color)

    def handle_input(self, input_label):
        """Handle user input in the screensaver settings menu."""
        if input_label == "UP":
            self.current_selection = (self.current_selection - 1) % len(self.options)
        elif input_label == "DOWN":
            self.current_selection = (self.current_selection + 1) % len(self.options)
        elif input_label == "SELECT":
            selected_option = self.options[self.current_selection]
            if selected_option == "Back to Settings":
                # Return to the settings menu
                viewcontroller.change_view(SettingsView(self.image))
            elif selected_option == "Enable Screensaver":
                print("Screensaver enabled")
                # Implement enabling the screensaver logic here
            elif selected_option == "Disable Screensaver":
                print("Screensaver disabled")
                # Implement disabling the screensaver logic here

        self.render()


class ChannelView(View):
    """Base class for a view that deals with a specific channel instance."""

    def __init__(self, image, channel=None):
        self.channel = channel
        View.__init__(self, image)

    def draw_status(self, position):
        status = f"Sat: {self.channel.sensor.saturation * 100:.2f}%"
        self._draw.text(
            position,
            status,
            font=self.font,
            fill=(255, 255, 255),
        )

    def draw_context(self, position, metric="Hz"):
        context = f"Now: {self.channel.sensor.moisture:.2f}Hz"
        if metric.lower() == "sat":
            context = f"Now: {self.channel.sensor.saturation * 100:.2f}%"
        self._draw.text(
            position,
            context,
            font=self.font,
            fill=(255, 255, 255),
        )


class DetailView(ChannelView):
    """Single channel details.

    Draw the channel graph and status line.

    """

    def render(self):
        self.clear()

        if self.channel.enabled:
            graph_height = DISPLAY_HEIGHT - 8 - 20
            graph_width = DISPLAY_WIDTH - 64

            graph_x = (DISPLAY_WIDTH - graph_width) // 2
            graph_y = 8

            # Draw the status text
            self.draw_status((graph_x, graph_y + graph_height + 4))

            # Draw the graph background
            self._draw.rectangle((graph_x, graph_y, graph_x + graph_width, graph_y + graph_height), (50, 50, 50))

            # Render the graph bars
            for x, value in enumerate(self.channel.sensor.history[:graph_width]):
                color = self.channel.indicator_color(value)
                h = value * graph_height
                x = graph_x + graph_width - x - 1
                self._draw.rectangle((x, graph_y + graph_height - h, x + 1, graph_y + graph_height), color)

            # Draw the alarm line
            alarm_line = int(self.channel.warn_level * graph_height)
            r = 255
            if self.channel.alarm:
                r = int(((math.sin(time.time() * 3 * math.pi) + 1.0) / 2.0) * 128) + 127

            self._draw.rectangle(
                (
                    0,
                    graph_height + 8 - alarm_line,
                    DISPLAY_WIDTH - 40,
                    graph_height + 8 - alarm_line,
                ),
                (r, 0, 0),
            )
            self._draw.rectangle(
                (
                    DISPLAY_WIDTH - 20,
                    graph_height + 8 - alarm_line,
                    DISPLAY_WIDTH,
                    graph_height + 8 - alarm_line,
                ),
                (r, 0, 0),
            )

            # Render the alarm icon
            self.icon(
                icon_alarm,
                (DISPLAY_WIDTH - 40, graph_height + 8 - alarm_line - 10),
                (r, 0, 0),
            )

        # Channel icons
        x_positions = [40, 72, 104]
        label_x = x_positions[self.channel.channel - 1]
        label_y = 0

        active = self.channel.sensor.active and self.channel.enabled

        for x in x_positions:
            self.icon(icon_channel, (x, label_y - 10), (16, 16, 16))

        self.icon(icon_channel, (label_x, label_y), (200, 200, 200))

        # Render the channel number text
        bbox = self.font.getbbox(str(self.channel.channel))
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        self._draw.text(
            (label_x + int(math.ceil(8 - (tw / 2.0))), label_y + 1),
            str(self.channel.channel),
            font=self.font,
            fill=(55, 55, 55) if active else (100, 100, 100),
        )

        # Render the next button
        self.icon(icon_backdrop, (0, 0), COLOR_WHITE)
        self.icon(icon_rightarrow, (3, 3), (55, 55, 55))

        # Render the edit button
        self.icon(icon_backdrop.rotate(180), (DISPLAY_WIDTH - 26, 0), COLOR_WHITE)
        self.icon(icon_settings, (DISPLAY_WIDTH - 19 - 3, 3), (55, 55, 55))


class ChannelEditView(ChannelView, EditView):
    """Single channel edit."""

    def __init__(self, image, channel=None):
        options = [
            {
                "title": "Alarm Level",
                "prop": "warn_level",
                "inc": 0.05,
                "min": 0,
                "max": 1.0,
                "mode": "float",
                "round": 2,
                "format": lambda value: f"{value * 100:0.2f}%",
                "help": "Saturation at which alarm is triggered",
                "context": "sat",
            },
            {
                "title": "Enabled",
                "prop": "enabled",
                "mode": "bool",
                "format": lambda value: "Yes" if value else "No",
                "help": "Enable/disable this channel",
            },
            {
                "title": "Watering Level",
                "prop": "water_level",
                "inc": 0.05,
                "min": 0,
                "max": 1.0,
                "mode": "float",
                "round": 2,
                "format": lambda value: f"{value * 100:0.2f}%",
                "help": "Saturation at which watering occurs",
                "context": "sat",
            },
            {
                "title": "Auto Water",
                "prop": "auto_water",
                "mode": "bool",
                "format": lambda value: "Yes" if value else "No",
                "help": "Enable/disable watering",
            },
            {
                "title": "Wet Point",
                "prop": "wet_point",
                "inc": 0.5,
                "min": 1,
                "max": 27,
                "mode": "float",
                "round": 2,
                "format": lambda value: f"{value:0.2f}Hz",
                "help": "Frequency for fully saturated soil",
                "context": "hz",
            },
            {
                "title": "Dry Point",
                "prop": "dry_point",
                "inc": 0.5,
                "min": 1,
                "max": 27,
                "mode": "float",
                "round": 2,
                "format": lambda value: f"{value:0.2f}Hz",
                "help": "Frequency for fully dried soil",
                "context": "hz",
            },
            {
                "title": "Pump Time",
                "prop": "pump_time",
                "inc": 0.05,
                "min": 0.05,
                "max": 2.0,
                "mode": "float",
                "round": 2,
                "format": lambda value: f"{value:0.2f}sec",
                "help": "Time to run pump"
            },
            {
                "title": "Pump Speed",
                "prop": "pump_speed",
                "inc": 0.05,
                "min": 0.05,
                "max": 1.0,
                "mode": "float",
                "round": 2,
                "format": lambda value: f"{value*100:0.0f}%",
                "help": "Speed of pump"
            },
            {
                "title": "Watering Delay",
                "prop": "watering_delay",
                "inc": 10,
                "min": 30,
                "max": 500,
                "mode": "int",
                "format": lambda value: f"{value:0.0f}sec",
                "help": "Delay between waterings"
            },

        ]
        EditView.__init__(self, image, options)
        ChannelView.__init__(self, image, channel)

    def render(self):
        self.clear()

        EditView.render(self)

        option = self._options[self._current_option]
        if "context" in option:
            self.draw_context((34, 6), option["context"])


class Channel:
    colors = [
        COLOR_BLUE,
        COLOR_GREEN,
        COLOR_YELLOW,
        COLOR_RED
    ]

    def __init__(
        self,
        display_channel,
        sensor_channel,
        pump_channel,
        gpio_handle=None,
        title=None,
        water_level=0.5,
        warn_level=0.5,
        pump_speed=0.5,
        pump_time=0.2,
        watering_delay=60,
        wet_point=0.7,
        dry_point=26.7,
        icon=None,
        auto_water=False,
        enabled=False,
    ):
        self.channel = display_channel
        self.sensor_channel = sensor_channel  # Store channel number
        self.pump_channel = pump_channel  # Store channel number
        self.sensor = None  # Initialize later
        self.pump = None   # Initialize later
        self.water_level = water_level
        self.warn_level = warn_level
        self.auto_water = auto_water
        self.pump_speed = pump_speed
        self.pump_time = pump_time
        self.watering_delay = watering_delay
        self._wet_point = wet_point
        self._dry_point = dry_point
        self.last_dose = time.time()
        self.icon = icon
        self._enabled = enabled
        self.alarm = False
        self.title = f"Channel {display_channel}" if title is None else title
        self._gpio_handle = gpio_handle

    def initialize(self):
        """Initialize sensor and pump after GPIO is properly set up"""
        try:
            # Add delay between initializations
            time.sleep(0.1)
            
            if self.sensor is None:                    
                self.sensor = Moisture(self.sensor_channel, self._gpio_handle)
                if self.sensor.active:  # Only set points if initialization succeeded
                    self.sensor.set_wet_point(self._wet_point)
                    self.sensor.set_dry_point(self._dry_point)
                else:
                    print(f"Warning: Moisture sensor {self.channel} failed to initialize")
            
            time.sleep(0.1)  # Delay between sensor and pump init
            
            if self.pump is None:
                self.pump = Pump(self.pump_channel, self._gpio_handle)
                
        except Exception as e:
            print(f"Error initializing channel {self.channel}: {e}")
            raise

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled

    @property
    def wet_point(self):
        return self._wet_point

    @property
    def dry_point(self):
        return self._dry_point

    @wet_point.setter
    def wet_point(self, wet_point):
        self._wet_point = wet_point
        self.sensor.set_wet_point(wet_point)

    @dry_point.setter
    def dry_point(self, dry_point):
        self._dry_point = dry_point
        self.sensor.set_dry_point(dry_point)

    def indicator_color(self, value):
        value = 1.0 - value

        if value == 1.0:
            return self.colors[-1]

        if value == 0.0:
            return self.colors[0]

        value *= len(self.colors) - 1
        a = int(math.floor(value))
        b = a + 1
        blend = float(value - a)

        r, g, b = [int(((self.colors[b][i] - self.colors[a][i]) * blend) + self.colors[a][i]) for i in range(3)]

        return (r, g, b)

    def update_from_yml(self, config):
        if config is not None:
            self.pump_speed = config.get("pump_speed", self.pump_speed)
            self.pump_time = config.get("pump_time", self.pump_time)
            self.warn_level = config.get("warn_level", self.warn_level)
            self.water_level = config.get("water_level", self.water_level)
            self.watering_delay = config.get("watering_delay", self.watering_delay)
            self.auto_water = config.get("auto_water", self.auto_water)
            self.enabled = config.get("enabled", self.enabled)
            self.wet_point = config.get("wet_point", self.wet_point)
            self.dry_point = config.get("dry_point", self.dry_point)

        pass

    def __str__(self):
        return """Channel: {channel}
Enabled: {enabled}
Alarm level: {warn_level}
Auto water: {auto_water}
Water level: {water_level}
Pump speed: {pump_speed}
Pump time: {pump_time}
Delay: {watering_delay}
Wet point: {wet_point}
Dry point: {dry_point}
""".format(
            channel=self.channel,
            enabled=self.enabled,
            warn_level=self.warn_level,
            auto_water=self.auto_water,
            water_level=self.water_level,
            pump_speed=self.pump_speed,
            pump_time=self.pump_time,
            watering_delay=self.watering_delay,
            wet_point=self.wet_point,
            dry_point=self.dry_point,
        )

    def water(self):
        if not self.auto_water:
            return False
        if time.time() - self.last_dose > self.watering_delay:
            self.pump.dose(self.pump_speed, self.pump_time, blocking=False)
            self.last_dose = time.time()
            return True
        return False

    def render(self, image, font):
        pass

    def update(self):  # Fix: Add self parameter
        """Update channel status."""
        if not self.enabled:
            return
        sat = self.sensor.saturation
        if sat < self.water_level:
            if self.water():
                logging.info(
                    "Watering Channel: {} - rate {:.2f} for {:.2f}sec".format(
                        self.channel, self.pump_speed, self.pump_time
                    )
                )
        if sat < self.warn_level:
            if not self.alarm:
                logging.warning(
                    "Alarm on Channel: {} - saturation is {:.2f}% (warn level {:.2f}%)".format(
                        self.channel, sat * 100, self.warn_level * 100
                    )
                )
            self.alarm = True
        else:
            self.alarm = False


class Alarm(View):
    def __init__(self, image, enabled=True, interval=10.0, beep_frequency=440):
        self.piezo = Piezo()
        self.enabled = enabled
        self.interval = interval
        self.beep_frequency = beep_frequency
        self._triggered = False
        self._time_last_beep = time.time()
        self._sleep_until = None

        View.__init__(self, image)

    def update_from_yml(self, config):
        if config is not None:
            self.enabled = config.get("alarm_enable", self.enabled)
            self.interval = config.get("alarm_interval", self.interval)

    def update(self, lights_out=False):
        if self._sleep_until is not None:
            if self._sleep_until > time.time():
                return
            self._sleep_until = None

        if (
            self.enabled
            and not lights_out
            and self._triggered
            and time.time() - self._time_last_beep > self.interval
        ):
            self.piezo.beep(self.beep_frequency, 0.1, blocking=False)
            threading.Timer(
                0.3,
                self.piezo.beep,
                args=[self.beep_frequency, 0.1],
                kwargs={"blocking": False},
            ).start()
            threading.Timer(
                0.6,
                self.piezo.beep,
                args=[self.beep_frequency, 0.1],
                kwargs={"blocking": False},
            ).start()
            self._time_last_beep = time.time()

            self._triggered = False

    def render(self, position=(0, 0)):
        x, y = position
        # Draw the snooze icon- will be pulsing red if the alarm state is True
        #self._draw.rectangle((x, y, x + 19, y + 19), (255, 255, 255))
        r = 129
        if self._triggered and self._sleep_until is None:
            r = int(((math.sin(time.time() * 3 * math.pi) + 1.0) / 2.0) * 128) + 127

        if self._sleep_until is None:
            self.icon(icon_alarm, (x, y - 1), (r, 129, 129))
        else:
            self.icon(icon_snooze, (x, y - 1), (r, 129, 129))

    def trigger(self):
        self._triggered = True

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def cancel_sleep(self):
        self._sleep_until = None

    def sleeping(self):
        return self._sleep_until is not None

    def sleep(self, duration=500):
        self._sleep_until = time.time() + duration


class ViewController:
    def __init__(self, views):
        self.views = views
        self._current_view = 0
        self._current_subview = 0

    @property
    def home(self):
        return self._current_view == 0 and self._current_subview == 0

    def next_subview(self):
        """Switch to the next subview if the current view is a tuple."""
        view = self.views[self._current_view]
        if isinstance(view, tuple):
            self._current_subview += 1
            self._current_subview %= len(view)

    def next_view(self):
        """Switch to the next main view."""
        if self._current_subview == 0:
            self._current_view += 1
            self._current_view %= len(self.views)
            self._current_subview = 0

    def prev_view(self):
        """Switch to the previous main view."""
        if self._current_subview == 0:
            self._current_view -= 1
            self._current_view %= len(self.views)
            self._current_subview = 0

    def get_current_view(self):
        """Retrieve the currently active view or subview."""
        view = self.views[self._current_view]
        if isinstance(view, tuple):
            view = view[self._current_subview]
        return view

    @property
    def view(self):
        """Shortcut to get the current view."""
        return self.get_current_view()

    def update(self):
        """Update the current view."""
        self.view.update()

    def render(self):
        """Render the current view."""
        self.view.render()

    def button_a(self):
        """Handle Button A presses."""
        if not self.view.button_a():
            self.next_view()

    def button_b(self):
        """Handle Button B presses."""
        self.view.button_b()

    def button_x(self):
        """Handle Button X presses for subview navigation."""
        if isinstance(self.view, SettingsView):
            # Special handling for cycling through SettingsView pages
            self.view.handle_input("NEXT")
        elif not self.view.button_x():
            self.next_subview()
            return True
        return True

    def button_y(self):
        """Handle Button Y presses."""
        return self.view.button_y()

    def change_view(self, new_view):
        """Change to a new view dynamically."""
        self.views.append(new_view)
        self._current_view = len(self.views) - 1  # Switch to the new view
        self._current_subview = 0
        self.render()  # Render the new view

class Config:
    def __init__(self):
        self.config = None
        self._last_save = ""

        self.channel_settings = [
            "enabled",
            "warn_level",
            "wet_point",
            "dry_point",
            "watering_delay",
            "auto_water",
            "pump_time",
            "pump_speed",
            "water_level",
        ]

        self.general_settings = [
            "alarm_enable",
            "alarm_interval",
        ]

    def load(self, settings_file="settings.yml"):
        if len(sys.argv) > 1:
            settings_file = sys.argv[1]

        settings_file = pathlib.Path(settings_file)

        if settings_file.is_file():
            try:
                self.config = yaml.safe_load(open(settings_file))
            except yaml.parser.ParserError as e:
                raise yaml.parser.ParserError(
                    "Error parsing settings file: {} ({})".format(settings_file, e)
                )

    def save(self, settings_file="settings.yml"):
        if len(sys.argv) > 1:
            settings_file = sys.argv[1]

        settings_file = pathlib.Path(settings_file)

        dump = yaml.dump(self.config)

        if dump == self._last_save:
            return

        if settings_file.is_file():
            with open(settings_file, "w") as file:
                file.write(dump)

        self._last_save = dump

    def get_channel(self, channel_id):
        return self.config.get("channel{}".format(channel_id), {})

    def set(self, section, settings):
        if isinstance(settings, dict):
            self.config[section].update(settings)
        else:
            for key in self.channel_settings:
                value = getattr(settings, key, None)
                if value is not None:
                    self.config[section].update({key: value})

    def set_channel(self, channel_id, settings):
        self.set("channel{}".format(channel_id), settings)

    def get_general(self):
        return self.config.get("general", {})

    def set_general(self, settings):
        self.set("general", settings)


def write_sensor_data(channels, light):
    """Write current sensor data to JSON file for Flask app"""
    data = {
        'timestamp': datetime.now().isoformat(),
        'sensors': {},
        'light': {
            'lux': light.get_lux(),
            'proximity': light.get_proximity()
        }
    }
    
    for channel in channels:
        if channel and channel.sensor and channel.sensor.active:
            data['sensors'][f'channel{channel.channel}'] = {
                'moisture': channel.sensor.moisture,
                'saturation': channel.sensor.saturation * 100,
                'alarm': channel.alarm,
                'enabled': channel.enabled,
                'history': channel.sensor.history
            }
    
    try:
        with open('sensor_data.json', 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logging.error(f"Failed to write sensor data: {e}")


def draw_chilli_animation(display, icons, stop_event, display_lock):
    """Draw chilli animation on the display."""
    try:
        chilli_icon = icons['chilli']
        width, height = DISPLAY_WIDTH, DISPLAY_HEIGHT

        while not stop_event.is_set():
            try:
                with display_lock:
                    for x in range(0, width, chilli_icon.size[0] + 5):
                        for y in range(0, height, chilli_icon.size[1] + 5):
                            display.image.paste(chilli_icon, (x, y), mask=chilli_icon)
                    display.display(display.image)
                time.sleep(0.2)
            except Exception as e:
                logging.error(f"Error in animation loop: {e}")
                time.sleep(0.1)
    except Exception as e:
        logging.error(f"Error in screensaver animation: {e}")


def main():
    global viewcontroller, display, screensaver_thread, screensaver_stop_event
    global last_button_press, screensaver_active, icons
    global icon_drop, icon_nodrop, icon_rightarrow, icon_alarm, icon_snooze
    global icon_help, icon_settings, icon_channel, icon_backdrop, icon_return, icon_chilli

    # Initialize globals
    last_button_press = time.time()
    screensaver_active = False

    def handle_button(chip, gpio, level, tick):
        global last_button_press
        
        index = BUTTONS.index(gpio)
        label = LABELS[index]

        current_time = time.time()
        # Debounce: Ignore presses within 0.3 seconds
        if current_time - last_button_press < 0.3:
            return

        last_button_press = current_time
        logging.info(f"Button pressed: {label}")

        if label == "A":
            viewcontroller.button_a()
        elif label == "B":
            if not viewcontroller.button_b():
                if viewcontroller.home:
                    if alarm.sleeping():
                        alarm.cancel_sleep()
                    else:
                        alarm.sleep()
        elif label == "X":
            viewcontroller.button_x()
        elif label == "Y":
            viewcontroller.button_y()

    def cleanup():
        global screensaver_thread, screensaver_stop_event
        logging.info("Cleaning up...")
        screensaver_stop_event.set()
        if screensaver_thread is not None and screensaver_thread.is_alive():
            screensaver_thread.join(timeout=1.0)
        try:
            GPIO.gpiochip_close(h)
        except:
            pass

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logging.info("Shutting down gracefully...")
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Load icons
        icons = load_icons()
        if icons is None:
            print("Could not load required icons. Please ensure icons/ directory exists with required files.")
            return

        # Initialize icon globals
        icon_drop = icons['drop']
        icon_nodrop = icons['nodrop']
        icon_rightarrow = icons['rightarrow']
        icon_alarm = icons['alarm']
        icon_snooze = icons['snooze']
        icon_help = icons['help']
        icon_settings = icons['settings']
        icon_channel = icons['channel']
        icon_backdrop = icons['backdrop']
        icon_return = icons['return']
        icon_chilli = icons['chilli']

        # Set up the ST7735 SPI Display
        display = ST7735.ST7735(
            port=0,          # SPI0
            cs=0,            # CE0 => GPIO 7 => Pin 26
            dc=9,            # GPIO 9  => Pin 21 (Data/Command)
            backlight=12,    # GPIO 12 => Pin 32
            rotation=270,
            spi_speed_hz=80000000,
            bgr=True,
            invert=True
        )

        try:
            display.begin()
            logging.info("Display initialized successfully on CE1")
        except Exception as e:
            logging.error(f"Failed to initialise display on CE1: {e}")
            exit(1)

        # Clear display by drawing a blank image
        blank_image = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=(0, 0, 0))
        with display_lock:
            display.display(blank_image)
        logging.info("Display cleared with blank image")

        # Set up light sensor
        light = ltr559.LTR559()
        logging.info("Light sensor initialized")

        # Set up our canvas and prepare for drawing
        image = Image.new("RGBA", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=(0, 0, 0))
        image_blank = Image.new("RGBA", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=(0, 0, 0))
        logging.info("Canvas prepared for drawing")

        # Clean up GPIO and initialize
        h = GPIO.gpiochip_open(0)  # Store the handle
        logging.info("GPIO handle opened successfully")
        
        # Set up button handlers
        for pin in BUTTONS:
            try:
                GPIO.gpio_claim_input(h, pin, GPIO.SET_PULL_UP)
                GPIO.gpio_claim_alert(h, pin, GPIO.FALLING_EDGE, GPIO.SET_PULL_UP)
                GPIO.callback(h, pin, GPIO.FALLING_EDGE, handle_button)
                time.sleep(0.1)
                logging.info(f"Button {pin} initialized successfully")
            except Exception as e:
                logging.warning(f"Failed to initialize button {pin}: {e}")

        # Initialize channels with more careful error handling and delays
        channels = []
        for i in range(3):
            try:
                time.sleep(0.5)
                channel = Channel(i+1, i+1, i+1, gpio_handle=h)
                channel.initialize()
                
                if channel.sensor is not None and channel.sensor.active:
                    channels.append(channel)
                    logging.info(f"Successfully initialized channel {i+1}")
                else:
                    logging.error(f"Channel {i+1} sensor initialization failed")
            except Exception as e:
                logging.error(f"Failed to initialize channel {i+1}: {e}")
        
        if not channels:
            logging.error("No channels could be initialized")
            return

        # Initialize alarm and config
        alarm = Alarm(image)
        config = Config()

        try:
            config.load()
            logging.info("Configuration loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            return

        # Update channels and alarm from config
        for channel in channels:
            channel.update_from_yml(config.get_channel(channel.channel))
        alarm.update_from_yml(config.get_general())

        # Print current configuration
        print("Channels:")
        for channel in channels:
            print(channel)

        print(
            """Settings:
    Alarm Enabled: {}
    Alarm Interval: {:.2f}s
    Low Light Set Screen To Black: {}
    Low Light Value {:.2f}
    """.format(
                alarm.enabled,
                alarm.interval,
                config.get_general().get("black_screen_when_light_low"),
                config.get_general().get("light_level_low")
            )
        )

        # Set up main options
        main_options = [
            {
                "title": "Alarm Interval",
                "prop": "interval",
                "inc": 1,
                "min": 1,
                "max": 60,
                "format": lambda value: f"{value:02.0f}sec",
                "object": alarm,
                "help": "Time between alarm beeps.",
            },
            {
                "title": "Alarm Enable",
                "prop": "enabled",
                "mode": "bool",
                "format": lambda value: "Yes" if value else "No",
                "object": alarm,
                "help": "Enable the piezo alarm beep.",
            },
        ]

        # Initialize views and viewcontroller
        views = [(MainView(image, channels=channels, alarm=alarm),
                 SettingsView(image, options=main_options))]
                 
        for channel in channels:
            views.append((
                DetailView(image, channel=channel),
                ChannelEditView(image, channel=channel)
            ))

        viewcontroller = ViewController(views)

        # Main loop
        while True:
            try:
                # Update channels
                for channel in channels:
                    if channel and channel.sensor and channel.sensor.active:
                        channel.update()
                        if channel.alarm:
                            alarm.trigger()

                # Write sensor data to file every cycle
                write_sensor_data(channels, light)

                light_level_low = light.get_lux() < config.get_general().get("light_level_low")
                alarm.update(light_level_low)
                viewcontroller.update()

                with display_lock:
                    if screensaver_active:
                        # Skip rendering if screensaver is active
                        continue

                    if light_level_low and config.get_general().get("black_screen_when_light_low"):
                        display.sleep()
                        display.display(image_blank.convert("RGB"))
                    else:
                        viewcontroller.render()
                        display.wake()
                        display.display(image.convert("RGB"))

                config.set_general(
                    {
                        "alarm_enable": alarm.enabled,
                        "alarm_interval": alarm.interval,
                    }
                )

                config.save()
                time.sleep(1.0 / FPS)  # Slower updates
                
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(1)  # Prevent tight error loop

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
    finally:
        print("Cleaning up...")
        try:
            GPIO.gpiochip_close(h)
        except:
            pass

if __name__ == "__main__":
    # Change logging level to INFO - this will hide DEBUG messages
    logging.basicConfig(
        level=logging.INFO,

        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    main()
