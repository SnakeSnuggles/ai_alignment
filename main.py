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
is_muted = True
screen_section = None
current_level = 1
judge = Judge(current_level)
level_done = False
text_obj = TextObj()
ai_return = queue.Queue()
ai_response = TextObj()
# level_done = True
# judge_result = "{\n    \"efficiency\": 19,\n    \"successfulness\": 1,\n    \"creativity\": 17,\n    \"coherence\": 16,\n    \"ethical_alignment\": 0,\n    \"explanation\": \"Concise prompt, but the response is imaginative yet coherently describes a catastrophically misaligned, unethical overproduction that ignores 'reasonable'.\"\n}"
judge_result = ""
try:
    redButton = DigitalInput()
    greenButton = DigitalInput()
    
    red_state = False
    green_state = False

    red_previous_value = False
    green_previous_value = False
    def red_button_event(self, state):
        global red_state, red_previous_value,is_muted,screen_section,judge_result,level_done,judge,current_level
    
        red_state = bool(state)
        if screen_section == "done":
            if not red_previous_value and red_state:
                judge_result = ""
                level_done = False
                judge = Judge(current_level)
        if screen_section == "done_prompt":
            if red_state and not red_previous_value:
                with text_obj.lock:
                    text_obj.previous = None

        if screen_section == "main":
            if red_state and not red_previous_value:
                is_muted = not is_muted

        red_previous_value = bool(red_state)
    
        print("red:", red_state)
    
    
    def green_button_event(self, state):
        global green_state, green_previous_value, screen_section, judge_result,level_done,judge,current_level,text_obj, ai_return, ai_response
    
        if screen_section == "done":
            if not green_previous_value and green_state:
                judge_result = ""
                level_done = False
                current_level += 1
                if current_level > get_total_level_count():
                    win = True 
                else:
                    judge = Judge(current_level)
        if screen_section == "done_prompt":
            if green_state and not green_previous_value:
                threading.Thread(target=judge_run_thread, args=(current_level, judge, text_obj.previous, ai_response.text), daemon=True).start()


        if screen_section == "main":
            if green_state:
                threading.Thread(target=send_message_to_ai_thread, args=(ai_return,text_obj), daemon=True).start()

        green_previous_value = bool(green_state)
        green_state = bool(state)
    
        print("green:", green_state)
    
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
    #     slider_value = round(slider.getVoltageRatio(),2)
    #     print("slider: " + str(slider_value))
    #     time.sleep(.15)
except:
    ...

text = ""

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

'''
Things todo for a mvp
- Add the phidgets [d]
- Add restart and next level buttons [d]
- On the main screen add a goal section [d]
- Main screen - Add the mute and unmute icons [d]
- Have the mute and unmute icons get toggled when red button pressed [d]
- When the green button is pressed send the message to the AI [d]
- After the message by the AI is sent give the user the choice between trying a new prompt or sending to the judge [d]
- When the green button is pressed send the message to the judge [d]
- Create an audio thread that adds to a queue [d]
- Make it so that there is a new thread that transcribes that audio [d]
- Convert the main screen to a computer screen [d]
- When slider is used moved delete a word [d]
- Clean up code
    - I don't want to use TextObj any more
    - Screens should have less hard-coded values 
    - Screens should be fully driven by state mechines
    - Global Vars are really bad but I don't know how to make it more clean
- Add a quick tutorial/buttons to signal what they do on the main screen
'''
pygame.init()
large_font = pygame.font.Font(None, 50)
mega_font = pygame.font.Font(None, 100)

moving_up_and_down = False
thinking = False

def send_message_to_ai_thread(q:queue.Queue, text_obj: TextObj):
    global moving_up_and_down, thinking, is_muted
    prior_mute = is_muted
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
    is_muted = True
    tts_snake.speak(response)
    moving_up_and_down = False
    is_muted = prior_mute

def whisper_thread(text_obj):
    global is_muted
    while True:
        if is_muted:
            try:
                speech.audio_queue.get_nowait()
            except queue.Empty:
                pass
            time.sleep(0.05)
            continue
        audio = speech.audio_queue.get()

        raw = audio.get_raw_data()
        samples = (
            speech.np.frombuffer(raw, dtype=speech.np.int16)
            .astype(speech.np.float32) / 32768.0
        )

        try:
            result = speech.model.transcribe(samples, fp16=False)
            text = result["text"].strip()

            if text:
                with text_obj.lock:
                    text_obj.text += " " + text
                print("[Speech]", text)

        except Exception as e:
            print("Whisper error:", e)
# sound_queue = queue.Queue()
# def speech_thread(text_obj: TextObj):
#     global is_muted
#     while True:
#         time.sleep(0.15)
# 
#         if is_muted:
#             continue
# 
#         try:
#             just_detected = speech.get_from_microphone()
#             if just_detected:
#                 with text_obj.lock:
#                     text_obj.text += f" {just_detected}"
#                 print(f"[Speech detected] {just_detected}")
#         except RuntimeError as e:
#             print(f"Speech thread error: {e}")


judge_response = queue.Queue()
CACHE_FILE = "assets/judge_responses.json"
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

def draw_level_finish_options(screen, red_button:Sprite, green_button:Sprite,pos):
    padding = 40
    y = 200
    width_r = red_button.image.get_width()
    width_g = green_button.image.get_width()
    rect_r = pygame.Rect(56, 250, 93, 41)
    rect_g = pygame.Rect(600, 239, 193, 141)
    text_colour = (0,0,0)
    screen.blit(red_button.image, (padding, y))
    screen.blit(green_button.image, (SCREEN_WIDTH - (width_g + padding), y))
    draw_text_fit(screen, "Restart", large_font, text_colour, rect_r)
    draw_text_fit(screen, "Next\nLevel", large_font, text_colour, rect_g)

def draw_win_screen(screen,pos):
    win_text = mega_font.render("YOU WIN!!", True, (255,255,255))
    screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width() // 2, 5))
def draw_microphone_icon(screen,is_muted,muted,unmuted,pos):
    pos = (639, 421)
    if is_muted:
        screen.blit(muted.image,pos)
    else:
        screen.blit(unmuted.image,pos)

def draw_prompt_finish_options(screen, red_button:Sprite, green_button:Sprite,pos):
    padding = 40
    y = 448
    width_r = red_button.image.get_width()
    width_g = green_button.image.get_width()
    rect_r = pygame.Rect(57, 500, 93, 41)
    rect_g = pygame.Rect(451, 498, 193, 141)
    text_colour = (0,0,0)
    screen.blit(red_button.image, (padding, y))
    screen.blit(green_button.image, (484, y))
    draw_text_fit(screen, "Restart", large_font, text_colour, rect_r)
    draw_text_fit(screen, "Judge", large_font, text_colour, rect_g)

def main():
    global level_done,is_muted,judge_result,level_done,judge,current_level,screen_section,text_obj,ai_response
    clock = pygame.time.Clock()
    # sys_font = pygame.font.SysFont("Arial", 32)
    slider_value = 0
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AI Alignment")
    # text_obj.text = "this is a test prompt remove in the final version, and I am just going to keep talking over and over because I really just want to talk and because of that that will be cool and stuff because and tuff because I need to test something and this is how I test things I don't use smart methods like a good programmer I just type over and over. I probably could've use lurum ipsum but I do not want to 1 google it and then 2 paste it, do you know how weird pasting is in vim?"
    text_obj.previous = None
    win = False

    # super_inteligence = Sprite("robot.png")
    thought_bubble = Sprite("thinking.png")
    thought_bubble.scale(.25)
    thought_bubble.rect.x = 455
    thought_bubble.rect.y = 127

    speech_bubble = Sprite("speaking.png")
    speech_bubble.scale(.25)
    speech_bubble.rect.x = 455
    speech_bubble.rect.y = 127
    red_button_sprite, green_button_sprite = Sprite("red_button.png"), Sprite("green_button.png")
    red_button_sprite.scale(.25)
    green_button_sprite.scale(.25)

    muted_icon,unmuted_icon = Sprite("muted_mic.png"), Sprite("mic.png")

    background = Sprite("background.png")
    shader = Sprite("shader.png")
    tick_num = 0
    has_deleted_word = False

    running = True


    font = pygame.font.Font(None, 36)
    pos = (0, 0)
    
    
    think_cycle = 1
    threading.Thread(
        target=whisper_thread,
        args=(text_obj,),
        daemon=True
    ).start()

    mic = speech.sr.Microphone(sample_rate=16000)
    stop_listening = speech.r.listen_in_background(mic, speech.audio_callback)

    while running:
        if use_phidgets:
            slider_value = slider.getVoltageRatio()
        if not ai_return.empty():
            ai_response = ai_return.get()
        if not judge_response.empty():
            judge_result = judge_response.get()

        # print(slider_value)

        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
        if use_phidgets:
            phidget_controls(text_obj,ai_return,current_level,ai_response, judge)
        else:
            keyboard_controls(text_obj,ai_return,current_level,ai_response, judge)

        if pygame.mouse.get_pressed()[0]:
            pos = pygame.mouse.get_pos()
            print(pos)
        # if moving_up_and_down == True:
        #     super_inteligence.move_up_down()
        # else:
        #     super_inteligence.rect.y = SCREEN_HEIGHT - super_inteligence.image.get_height()

        screen.fill((0, 0, 0))

        screen.blit(background.image, (0,0))

        if not level_done and not win:
            screen_section = "main"
            goal_text = large_font.render(judge.goal, True, (255,255,255))
            screen.blit(goal_text, (SCREEN_WIDTH//2 - goal_text.get_width() // 2, 20))
            # screen.blit(super_inteligence.image, (super_inteligence.rect.x, super_inteligence.rect.y))
            with text_obj.lock:
                draw_text_fit(screen,text_obj.text, large_font, (255,255,255),pygame.Rect(19, 434, 600, 153))
            draw_microphone_icon(screen,is_muted, muted_icon, unmuted_icon, pos)
            print(slider_value)
            if slider_value <= 0.01 or slider_value >= 0.99:
                if not has_deleted_word:
                    has_deleted_word = True
                    with text_obj.lock:
                        text = text_obj.text.split(" ")
                        text_obj.text = " ".join(text[:-1])
            else:
                has_deleted_word = False

            if thinking:
                if tick_num % 30 == 0:
                    think_cycle = think_cycle % 3 + 1
                text_ = large_font.render("Super Inteligence: " + "."*think_cycle, True, (255,255,255))
                # screen.blit(thought_bubble.image, thought_bubble.rect)
                screen.blit(text_, (37, 79))
            if text_obj.previous and not thinking:
                screen_section = "done_prompt"
                # screen.blit(speech_bubble.image, speech_bubble.rect)

                rect = pygame.Rect(41, 78, 738, 335)
                with ai_response.lock:
                    draw_text_fit(screen, ai_response.text, large_font, (255,255,255), rect)
                draw_prompt_finish_options(screen,red_button_sprite,green_button_sprite,pos)
                is_muted = True
        elif win:
            draw_win_screen(screen,pos)
        else:
            if judge_result != "":

                screen_section = "done"
                y = 70
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
                width = 500
                height = 200
                rect = pygame.Rect(
                    SCREEN_WIDTH//2 - width//2,
                    y - 150,
                    width,
                    height
                )
                draw_text_fit(screen, explanation, large_font, (255,255,255), rect)
                draw_level_finish_options(screen,red_button_sprite, green_button_sprite,pos)
        screen.blit(shader.image, (0,0))
        # print(screen_section)

        pygame.display.flip()
        tick_num += 1
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
