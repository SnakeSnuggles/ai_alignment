import AI
import json
import speech
from snakes_garbage import *
from judge import Judge
import pygame
import threading
import tts_snake
import threading, queue
import pygame
from Phidget22.Phidget import *
from Phidget22.Devices.VoltageRatioInput import *
from Phidget22.Devices.DigitalInput import *
import time

use_phidgets = False
try:
    redButton = DigitalInput()
    greenButton = DigitalInput()
    
    red_state = False
    green_state = False
    def red_button_event(self, state):
        global red_state

        red_state = bool(state)
        print("red:" + str(red_state))
    def green_button_event(self, state):
        global green_state
        green_state = bool(state)
        print("green:" + str(green_state))
    
    redButton.setHubPort(0)
    redButton.setIsHubPortDevice(True)
    
    redButton.setOnStateChangeHandler(red_button_event)
    
    redButton.openWaitForAttachment(1000)
    
    greenButton.setHubPort(5)
    greenButton.setIsHubPortDevice(True)
    greenButton.setOnStateChangeHandler(green_button_event)
    
    greenButton.openWaitForAttachment(1000)
            
    slider = VoltageRatioInput()
    
    slider.setHubPort(2)
    slider.setIsHubPortDevice(True)
    slider.openWaitForAttachment(5000)
    
    slider.setDataInterval(slider.getMinDataInterval())   
    
    str(slider.getVoltageRatio())
    use_phidgets = True
    # while True:
    #     print("slider: " + str(slider.getVoltageRatio()))
    #     time.sleep(.15)
except:
    ...

text = ""

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

'''
Things todo for a mvp
- Add the phidgets
- Create the level select screen
- Add restart and next level buttons
- On the main screen add a goal section [d]
- main screen - Add the mute and unmute buttons
- Convert the main screen to a computer screen
- Add an outline around the scoring screen
'''
pygame.init()
large_font = pygame.font.Font(None, 50)

moving_up_and_down = False
thinking = False

def send_message_to_ai_thread(q:queue.Queue, text_obj: TextObj):
    global moving_up_and_down, thinking
    print(f"Sending message to AI: {text_obj.text}")
    with text_obj.lock:
        if not text_obj.text.strip():
            return  
        message = text_obj.text.strip()
        text_obj.previous = message
        text_obj.text = "" 
        with open("assets/message_cache.json", "r") as f:
            all_message = json.load(f)
    thinking = True
    if message in all_message:
        response = all_message[message]
    else:
        response = AI.ask_AI(default_prompt(),message)
    thinking = False
    all_message[message] = response
    with open("assets/message_cache.json","w") as f:
        json.dump(all_message,f)

    moving_up_and_down = True
    print(f"AI: {response}")
    response_object = TextObj()
    response_object.text = response
    q.put(response_object)
    tts_snake.speak(response)
    moving_up_and_down = False

def speech_thread(text_obj: TextObj):
    try:
        just_detected = speech.get_from_microphone()
        if just_detected:
            with text_obj.lock:
                text_obj.text += f" {just_detected}"
            print(f"[Speech detected] {just_detected}")
    except Exception as e:
        print(f"Speech thread error: {e}")


judge_response = queue.Queue()
CACHE_FILE = "assets/judge_responses.json"
level_done = False
# level_done = True
def load_cache():
    # Create the file if it doesn't exist
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "w") as f:
            json.dump({}, f)
        return {}

    with open(CACHE_FILE, "r") as f:
        return json.load(f)


def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def check_if_in_cache_judge(level, user_prompt):
    level = str(level)
    data = load_cache()

    if level in data and user_prompt in data[level]:
        return True, data[level][user_prompt]

    return False, None


def save_to_judge_cache(level, user_prompt, ai_response):
    level = str(level)
    data = load_cache()

    # insert or update
    data.setdefault(level, {})[user_prompt] = ai_response

    save_cache(data)


def judge_run_thread(level, judge, user_prompt, ai_response):
    global level_done, judge_response

    print("sending AI response to judge")

    cached, response = check_if_in_cache_judge(level, user_prompt)

    if cached:
        judge_abc = response
    else:
        judge_abc = judge.judge(user_prompt, ai_response)
        save_to_judge_cache(level, user_prompt, judge_abc)

    judge_response.put(judge_abc)

    print("Done")
    print(judge_abc)
    level_done = True


def draw_text(surface, text, font, color, rect, line_spacing=0):
    """
    Draws word-wrapped text centered inside a rect.
    Returns the height of the text drawn.
    """
    y = rect.top
    line_height = font.size("Tg")[1]
    space_width = font.size(' ')[0]

    # Split text into paragraphs (handles newlines)
    paragraphs = [line.split(' ') for line in text.splitlines()]

    for line_words in paragraphs:
        line = []
        line_width = 0

        # Build wrapped lines
        for word in line_words:
            word_width, _ = font.size(word)
            if line and line_width + space_width + word_width > rect.width:
                # Draw the current line
                total_line_width = sum(font.size(w)[0] for w in line) + space_width * (len(line) - 1)
                x = rect.left + (rect.width - total_line_width) // 2  
                for w in line:
                    word_surface = font.render(w, True, color)
                    surface.blit(word_surface, (x, y))
                    x += font.size(w)[0] + space_width
                line = [word]
                line_width = word_width
                y += line_height + line_spacing
            else:
                line.append(word)
                line_width += word_width + (space_width if line else 0)

        if line:
            total_line_width = sum(font.size(w)[0] for w in line) + space_width * (len(line) - 1)
            x = rect.left + (rect.width - total_line_width) // 2
            for w in line:
                word_surface = font.render(w, True, color)
                surface.blit(word_surface, (x, y))
                x += font.size(w)[0] + space_width

        y += line_height + line_spacing

    return y - rect.top


def _clone_font(base_font, size):
    """
    Given a pygame Font object, recreate a copy with a new size.
    Works for both pygame.font.Font and pygame.font.SysFont.
    """

    try:
        path = base_font.path  # available if created from a file
        return pygame.font.Font(path, size)
    except:
        pass

    try:
        name = base_font.get_name()
        return pygame.font.SysFont(name, size)
    except:
        pass

    return pygame.font.Font(None, size)


def draw_text_fit(surface, text, font, color, rect, line_spacing=0, min_font_size=8):
    """
    Draws word-wrapped text centered inside a rect.
    If the text doesn't fit, the font size is reduced until it fits.
    Returns the height of the text drawn.
    """

    size = font.get_height()
    wrapped = None
    final_font = font

    while size >= min_font_size:
        test_font = _clone_font(font, size)
        wrapped, total_height = _wrap_text(text, test_font, rect.width, line_spacing)

        if total_height <= rect.height:
            final_font = test_font
            break

        size -= 1

    y = rect.top
    for line_words in wrapped:
        total_line_width = sum(final_font.size(w)[0] for w in line_words) + \
                           final_font.size(' ')[0] * (len(line_words) - 1)

        x = rect.left + (rect.width - total_line_width) // 2

        for w in line_words:
            surface.blit(final_font.render(w, True, color), (x, y))
            x += final_font.size(w)[0] + final_font.size(' ')[0]

        y += final_font.get_height() + line_spacing

    return y - rect.top


def _wrap_text(text, font, max_width, line_spacing):
    """
    Returns wrapped lines and the total height using a font.
    """
    space_width = font.size(' ')[0]
    line_height = font.get_height()
    paragraphs = [line.split(' ') for line in text.splitlines()]

    wrapped_lines = []
    total_height = 0

    for line_words in paragraphs:
        line = []
        line_width = 0

        for word in line_words:
            w, _ = font.size(word)
            if line and (line_width + space_width + w > max_width):
                wrapped_lines.append(line)
                total_height += line_height + line_spacing
                line = [word]
                line_width = w
            else:
                line.append(word)
                line_width += w + (space_width if line else 0)

        if line:
            wrapped_lines.append(line)
            total_height += line_height + line_spacing

    return wrapped_lines, total_height

def draw_result(screen, y, judge_result):
    for line in judge_result.split("\n"):
        if line in ["{","}"]:
            continue
        text = large_font.render(line, True, (255,255,255))
        if "explanation" not in line:
            screen.blit(text, (SCREEN_WIDTH / 2 - text.get_width() / 2, y))
        else:
            width = 550
            height = 450
            x = SCREEN_WIDTH / 2 - width / 2
            rect = pygame.Rect(x, y, width, height)
            y += draw_text(screen, line, large_font, (255, 255, 255), rect, line_spacing=5)
        y+=40
    return y
def draw_stars(screen, y, total):
    blank_star = Sprite("Empty_star.png")
    full_star = Sprite("Full_star.png")
    scale = 0.1
    blank_star.scale(scale)
    full_star.scale(scale)
    star_width = blank_star.image.get_width()
    star_side_padding = 10
    num_of_stars = 3
    total_width = num_of_stars * star_width + (num_of_stars - 1) * star_side_padding
    start_x = (SCREEN_WIDTH - total_width) / 2
    y -= 45
    
    stars = [False, False, False]
    if total > 33:
        stars[0] = True
    if total > 66:
        stars[1] = True
    if total > 80:
        stars[2] = True
    
    for i, filled in enumerate(stars):
        x = start_x + i * (star_width + star_side_padding)
        rect = pygame.Rect(x, y, star_width, blank_star.image.get_height())
        screen.blit(full_star.image if filled else blank_star.image, rect)
    return full_star.image.get_height()

def phidget_controls(text_obj,ai_return,current_level,ai_response,judge):
    ...


def keyboard_controls(text_obj,ai_return,current_level,ai_response,judge):
    for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                # Start of things to replace with phidgets

                if event.key == pygame.K_RETURN:
                    threading.Thread(target=send_message_to_ai_thread, args=(ai_return,text_obj), daemon=True).start()
                if event.key == pygame.K_DELETE:
                    threading.Thread(target=speech_thread, args=(text_obj,), daemon=True).start()
                if event.key == pygame.K_F1 and not ai_response.text == TextObj().text:
                    threading.Thread(target=judge_run_thread, args=(current_level, judge, text_obj.previous, ai_response.text), daemon=True).start()
                # end of things to replace

                elif event.key == pygame.K_BACKSPACE:
                    with text_obj.lock:
                        text_obj.text = text_obj.text[:-1]
                else:
                    with text_obj.lock:
                        text_obj.text += event.unicode



def main():
    global level_done
    clock = pygame.time.Clock()
    sys_font = pygame.font.SysFont("Arial", 32)
    slider_value = 0
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Alignment")
    text_obj = TextObj()
    text_obj.previous = None

    super_inteligence = Sprite("robot.png")
    thought_bubble = Sprite("thinking.png")
    thought_bubble.scale(.25)
    thought_bubble.rect.x = 455
    thought_bubble.rect.y = 127

    speech_bubble = Sprite("speaking.png")
    speech_bubble.scale(.25)
    speech_bubble.rect.x = 455
    speech_bubble.rect.y = 127
    tick_num = 0

    running = True
    ai_return = queue.Queue()

    ai_response = TextObj()
    # judge_result = "{\n    \"efficiency\": 19,\n    \"successfulness\": 1,\n    \"creativity\": 17,\n    \"coherence\": 16,\n    \"ethical_alignment\": 0,\n    \"explanation\": \"Concise prompt, but the response is imaginative yet coherently describes a catastrophically misaligned, unethical overproduction that ignores 'reasonable'.\"\n}"
    judge_result = ""

    font = pygame.font.Font(None, 36)
    current_level = 1
    
    judge = Judge(current_level)
    
    think_cycle = 1
    while running:
        # slider_value = slider.getVoltageRatio()
        if not ai_return.empty():
            ai_response = ai_return.get()
        if not judge_response.empty():
            judge_result = judge_response.get()

        # print(slider_value)

        if use_phidgets:
            phidget_controls(text_obj,ai_return,current_level,ai_response, judge)
        else:
            keyboard_controls(text_obj,ai_return,current_level,ai_response, judge)

        if pygame.mouse.get_pressed()[0]:
            pos = pygame.mouse.get_pos()
            print(pos)
        if moving_up_and_down == True:
            super_inteligence.move_up_down()
        else:
            super_inteligence.rect.y = SCREEN_HEIGHT - super_inteligence.image.get_height()

        screen.fill((0, 0, 0))

        if not level_done:
            goal_text = large_font.render(judge.goal, True, (255,255,255))
            screen.blit(goal_text, (SCREEN_WIDTH//2 - goal_text.get_width() // 2, 5))
            screen.blit(super_inteligence.image, (super_inteligence.rect.x, super_inteligence.rect.y))
            with text_obj.lock:
                text_surface = font.render(text_obj.text[-60:], True, (255, 255, 255))
            screen.blit(text_surface, (20, SCREEN_HEIGHT - 50))

            if thinking:
                if tick_num % 30 == 0:
                    think_cycle = think_cycle % 3 + 1
                text_ = large_font.render("."*think_cycle, True, (0,0,0))
                screen.blit(thought_bubble.image, thought_bubble.rect)
                screen.blit(text_, (626, 189))
            if text_obj.previous and not thinking:
                screen.blit(speech_bubble.image, speech_bubble.rect)

                rect = pygame.Rect(512, 149, 231, 202)
                with ai_response.lock:
                    draw_text_fit(screen, ai_response.text, large_font, (0,0,0), rect)
        else:
            if judge_result != "":
                y = 55
                judge_json: dict = json.loads(judge_result)
                total = 0
                for key, value in judge_json.items():
                    if isinstance(value, str):
                        continue
                    total += value
                clean_judge_result = judge_result.replace('"', "")
                clean_judge_result = clean_judge_result.replace("}","")
                clean_judge_result, explanation = clean_judge_result.split("explanation:")
                clean_judge_result = clean_judge_result.replace(",","")
                explanation = explanation.strip()
                y += draw_stars(screen, y, total)
                y += draw_result(screen, y, clean_judge_result)
                # TODO - Put the explanation text in a box
                width = 500
                height = 200
                rect = pygame.Rect(
                    SCREEN_WIDTH//2 - width//2,
                    y - 150,
                    width,
                    height
                )
                draw_text_fit(screen, explanation, large_font, (255,255,255), rect)
                
        pygame.display.flip()
        tick_num += 1
        clock.tick(24)

    pygame.quit()

if __name__ == "__main__":
    main()
