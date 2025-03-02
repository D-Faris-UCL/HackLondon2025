from nicegui import ui, app, events

import summariser
import checker
import re
from quote_replace import QuoteReplacer

app.add_static_files('/static', 'static')

input_container = None
spinner_container = None
input_mode = None
summarise_button = None
url_field = None
summary_box = None
emoji_button = None
length_slider = None
uploaded_file = None
text_area = None
hallucination_check = None


css_styles = '''
body {
    background-color: #c7eae4;
    background-image: url('/static/Plant.png');
    background-repeat: no-repeat;
    background-position: bottom left;
    background-size: 200px;
}
'''

def handle_upload(e: events.UploadEventArguments):
    global uploaded_file
    text = e.content.read().decode('utf-8')
    uploaded_file = text


def show_input():
    global input_container, input_mode, summarise_button, url_field, summary_box, spinner_container, emoji_button, length_slider, uploaded_file, text_area, hallucination_check

    input_container.clear()
    with input_container:
        if input_mode.value == "Upload file":
            ui.space()
            ui.upload(on_upload=handle_upload,auto_upload=True).style("width:80%")
            ui.space()
        elif input_mode.value == "Add URL":
            url_field = ui.input(label="Link", placeholder="https://link-to-your-website").style('width:100%').props('outlined')
        elif input_mode.value == "Add text":
            text_area = ui.textarea(label="Your text").style('width:100%').props('outlined')

def split_quotes_with_newlines(text, min_quote_length=3):
    # Split the text by newlines first
    lines = text.split('\n')
    final_result = []
    
    for line in lines:
        if not line.strip():  # Skip empty lines or lines with only whitespace
            continue
            
        # Process quotes in this line
        quoted_sections = re.finditer(r'"([^"]*)"', line)
        
        # Build a list of sections to keep separate or merge
        sections = []
        last_end = 0
        
        for match in quoted_sections:
            quoted_content = match.group(1)
            
            # If there's non-quoted text before this quote, add it
            if match.start() > last_end:
                sections.append((line[last_end:match.start()], False))
            
            # Check if quoted content meets minimum length
            if len(quoted_content) >= min_quote_length:
                sections.append((f'"{quoted_content}"', True))
            else:
                sections.append((f'"{quoted_content}"', False))
            
            last_end = match.end()
        
        # Add any remaining text after the last quote
        if last_end < len(line):
            sections.append((line[last_end:], False))
        
        # Merge adjacent non-quote sections
        line_result = []
        current_non_quote = ""
        
        for content, is_quote in sections:
            if is_quote:
                if current_non_quote:
                    line_result.append(current_non_quote)
                    current_non_quote = ""
                line_result.append(content)
            else:
                current_non_quote += content
        
        if current_non_quote:
            line_result.append(current_non_quote)
        
        # Add results from this line to the final result
        final_result.extend(line_result)
    
    return final_result


async def generate_summary():
    global input_container, input_mode, summarise_button, url_field, summary_box, spinner_container, emoji_button, length_slider, uploaded_file, text_area, hallucination_check
    text = ""
    
    if input_mode.value == "Upload file":
        text = uploaded_file
    elif input_mode.value == "Add URL":
        text = summariser.get_website_text(url_field.value)
        ui.notify("URL loaded!!")
    elif input_mode.value == "Add text":
        text = text_area.value
    summary_box.clear()
    with summary_box:
        ui.markdown("Processing text...").style('margin-left:10px ; margin-right:10px')
    with spinner_container:
        ui.spinner(size='lg')
    
    while True:
        markdown = await summariser.process_legal_text(text, emoji_button.value, length_slider.value)
        if hallucination_check.value:
            if checker.check(text, markdown):
                break
        else:
            break
    replacer = QuoteReplacer(markdown)

    print(markdown)
    matches = [m.group(1) for m in re.finditer(r'""(.*?)""', markdown)]
    approx_quotes = [quote for quote in matches if len(quote) >= 50]
    
    for quote in approx_quotes:
        exact_quote = replacer.find_exact_quote(quote)
        markdown = markdown.replace(quote, exact_quote)
    # print(markdown)
    summary_box.clear()
    
    result = split_quotes_with_newlines(markdown, 50)
    with summary_box:
        for t in result:
            if t.strip():
                if t.startswith('"') and t.endswith('"'):
                    ui.link(t, "#").style('margin-left:10px ; margin-right:10px ; margin-top:0px; margin-bottom:0px; color:black')
                else:
                    ui.markdown(t).style('margin-left:10px ; margin-right:10px ; margin-top:0px; margin-bottom:0px')
    spinner_container.clear()


def handle_click(line_number):
    ui.notify(f'Line {line_number} clicked')

@ui.page('/')
def main_page():
    global input_container, input_mode, summarise_button, url_field, summary_box, spinner_container, emoji_button, length_slider, uploaded_file, text_area, hallucination_check

    ui.add_head_html(f'<style>{css_styles}</style>')

    with ui.header().style('background-color:white; color:black'):
        with ui.row().style('width:100%; margin-left:10px; margin-right:10px; font-size: 15px; margin-bottom:3px; margin-top:3px'):
            ui.label("About Us")
            ui.label("FAQ")
            ui.label("T&C")
    
    with ui.row().classes('w-full items-center').style('justify-content: right'):
        ui.label("Lexis Docklet").style('font-size:60px; margin-left:160px; font-weight: bold')
        ui.space()
        ui.image("Friendly.png").style('width:400px; margin-right:160px; border-radius: 0.6rem')
        
    with ui.row().classes('w-full').style('justify-content: center; align-items: center'):
        with ui.card().style('width:100%; margin-left:100px; margin-right:100px; border-radius: 1.5rem'):
            input_mode = ui.toggle(["Upload file", "Add URL", "Add text"],value="Upload file",on_change=show_input).props('color=teal')
            input_container = ui.column()
            input_container.style('width:100%; align-items: center')
            with input_container:
                ui.space()
                ui.upload(on_upload=handle_upload,auto_upload=True).style("width:80%")
                ui.space()
            emoji_button = ui.checkbox('Allow Emojis 😉')
            with ui.row().classes('no-wrap w-full'):
                percent_label = ui.label()
                length_slider = ui.slider(min=5, max=15, value=10).style('width:30%')
                percent_label.bind_text_from(length_slider, 'value', backward=lambda a: f'Summary length: {a}%')
            with ui.row():
                summarise_button = ui.button("Summarize!", color='#ffd972', on_click=generate_summary)
                hallucination_check = ui.checkbox('Reject hallucination')

        with ui.card().style('width:100%; margin-left:100px; margin-right:100px; border-radius: 1.5rem'):
            with ui.row():
                ui.label("Summary").style('font-weight: bold; font-size: 24px')
                spinner_container = ui.column()

            summary_box = ui.card().style('width:100%')

ui.run(host="0.0.0.0", reload=False, port=8080,title="Home")