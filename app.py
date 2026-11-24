import os
import gradio as gr
from PIL import Image, ImageOps
import requests
import io
import base64

# RunPod Serverless Configuration (reads from Render Environment Variables first)
RUNPOD_ENDPOINT = os.environ.get(
    "RUNPOD_ENDPOINT",
    "https://api.runpod.ai/v2/tb4lxwh2ef4izd/runsync"
)
RUNPOD_API_KEY = os.environ.get(
    "RUNPOD_API_KEY",
    "rpa_YMHX07T6KT0G5VB8HBU9363EMWS8PK01JSXJBY8U1r9t4i"
)

# Import Master Prompts safely
try:
    from prompts_config import MASTER_PROMPTS
except ImportError:
    MASTER_PROMPTS = {}

# Import Text Prompt Config safely
try:
    from textprompts_config import QUICK_RETOUCH_SLASH_COMMANDS
except ImportError:
    QUICK_RETOUCH_SLASH_COMMANDS = {}

# Import Preset Templates safely
try:
    from preset_prompts_config import PRESET_TEMPLATES_DB
except ImportError:
    PRESET_TEMPLATES_DB = {}

logo_path = "final_logo.png" if os.path.exists("final_logo.png") else None
favicon_path = "favicon.png" if os.path.exists("favicon.png") else logo_path

def get_base64(file_path):
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return ""
    return ""

logo_b64 = get_base64(logo_path)
favicon_b64 = get_base64(favicon_path)
bg_b64 = get_base64("bg.png")

if logo_b64:
    logo_src = "data:image/png;base64," + logo_b64
    logo_element = '<img src="' + logo_src + '" alt="AccPixelForge Logo" style="height: 50px; margin-right: 15px;">'
else:
    logo_element = '<span style="font-size: 24px; font-weight: 800; color: #ff6b00;">AccPixelForge</span>'

favicon_data_uri = f"data:image/png;base64,{favicon_b64}" if favicon_b64 else ""
favicon_head_html = (
    f'<link rel="icon" type="image/png" href="{favicon_data_uri}">\n'
    f'<link rel="shortcut icon" type="image/png" href="{favicon_data_uri}">'
    if favicon_data_uri else ""
)

# Checkpoint Models list
checkpoint_models_list = [
    "epicrealismXL_pureFix.safetensors",
    "cyberrealisticXL_v100_pruned_fp16.safetensors",
    "RealVisXL_V4.0.safetensors",
    "realvisxlV50_v50LightningBakedvae_full_fp16.safetensors"
]

# LoRA Models list
lora_models_list = [
    "None",
    "epicRealismXL-KiSSEnhancer_Lora.safetensors"
]

# Upscaler Models list
upscaler_models_list = [
    "None",
    "RealESRGAN_x4plus.pth",
    "4x-UltraSharp.pth",
    "codeformer.pth"
]

# Video Render Quality Options
video_render_quality_list = [
    "720p Standard HD (Fast Processing)",
    "1080p Full HD (Film Grade Render)",
    "4K Ultra Cinematic (Masterpiece Resolution)"
]

# Video Aspect Ratios List
video_aspect_ratios_list = [
    "16:9 (Landscape Cinematic)",
    "9:16 (Vertical Reel / TikTok)",
    "21:9 (Anamorphic Ultrawide)"
]

aspect_ratios_list = [
    "1:1 (1024x1024 Square)",
    "16:9 (1280x720 Landscape)",
    "9:16 (720x1280 Vertical/Reel)",
    "4:3 (1024x768 Standard)",
    "3:4 (768x1024 Portrait)",
    "21:9 (1536x640 Cinematic Ultrawide)",
    "9:21 (640x1536 Tall Vertical)",
    "3:2 (1200x800 Classic Photo)",
    "2:3 (800x1200 Photo Portrait)",
    "5:4 (1280x1024 Monitor)",
    "4:5 (1024x1280 Instagram)",
    "2:1 (1536x768 Wide)"
]

aspect_ratio_dimensions_map = {
    "1:1 (1024x1024 Square)": (1024, 1024),
    "16:9 (1280x720 Landscape)": (1280, 720),
    "9:16 (720x1280 Vertical/Reel)": (720, 1280),
    "4:3 (1024x768 Standard)": (1024, 768),
    "3:4 (768x1024 Portrait)": (768, 1024),
    "21:9 (1536x640 Cinematic Ultrawide)": (1536, 640),
    "9:21 (640x1536 Tall Vertical)": (640, 1536),
    "3:2 (1200x800 Classic Photo)": (1200, 800),
    "2:3 (800x1200 Photo Portrait)": (800, 1200),
    "5:4 (1280x1024 Monitor)": (1280, 1024),
    "4:5 (1024x1280 Instagram)": (1024, 1280),
    "2:1 (1536x768 Wide)": (1536, 768),
}

art_style_suffix_map = {
    "None": "",
    "Photorealistic": "photorealistic, ultra detailed photography, natural lighting, 8k",
    "Cinematic": "cinematic film still, dramatic lighting, anamorphic lens, 8k",
    "Oil Painting": "rich oil painting on canvas, visible brush strokes, fine art",
    "Anime": "high quality anime illustration, vibrant colors, crisp linework",
    "Cyberpunk": "cyberpunk futuristic neon aesthetic, moody sci-fi lighting, 8k",
    "3D Render": "3d render, octane render, unreal engine 5, studio lighting"
}

def update_dimensions_from_preset(selected_ratio):
    w, h = aspect_ratio_dimensions_map.get(selected_ratio, (1024, 1024))
    return w, h

def mock_transcribe(audio_file):
    if not audio_file:
        return ""
    return "A cinematic futuristic city with glowing neon lights and flying cars, highly detailed 8k resolution"

def auto_translate_prompt(text):
    if not text:
        return ""
    return f"High quality professional cinematic prompt translated from regional input: {text}, highly detailed masterpiece"

def load_preset_template(template_name):
    return PRESET_TEMPLATES_DB.get(template_name, "Cinematic masterpiece prompt")

def auto_composite_storyboard_grid(img1, img2, img3, img4, img5, img6):
    images = [img for img in [img1, img2, img3, img4, img5, img6] if img is not None]
    if not images:
        return None

    target_size = (384, 384)
    resized_imgs = [img.convert("RGB").resize(target_size) for img in images]

    cols = min(len(resized_imgs), 3)
    rows = (len(resized_imgs) + cols - 1) // cols

    grid_w = cols * target_size[0]
    grid_h = rows * target_size[1]

    grid_image = Image.new("RGB", (grid_w, grid_h), (15, 23, 42))
    for idx, img in enumerate(resized_imgs):
        r = idx // cols
        c = idx % cols
        grid_image.paste(img, (c * target_size[0], r * target_size[1]))

    return grid_image

def auto_composite_dynamic_grid(img1, img2, img3):
    images = [img for img in [img1, img2, img3] if img is not None]
    if not images:
        return None

    target_size = (512, 512)
    resized_imgs = [img.convert("RGB").resize(target_size) for img in images]

    cols = min(len(resized_imgs), 3)
    rows = (len(resized_imgs) + cols - 1) // cols

    grid_w = cols * target_size[0]
    grid_h = rows * target_size[1]

    grid_image = Image.new("RGB", (grid_w, grid_h), (15, 23, 42))
    for idx, img in enumerate(resized_imgs):
        r = idx // cols
        c = idx % cols
        grid_image.paste(img, (c * target_size[0], r * target_size[1]))

    return grid_image

def generate_image(
    prompt,
    neg_prompt="blurry, low quality, deformed",
    width=1024,
    height=1024,
    steps=30,
    cfg=7.5,
    seed=42,
    model_name="epicrealismXL_pureFix.safetensors",
    task="t2i",
    init_image=None,
    upscaler="None",
    style_preset="None",
    lora_name="None",
    lora_strength=0.75,
    quality_grade=None,
    aspect_ratio_label=None
):
    final_prompt = prompt or ""
    style_suffix = art_style_suffix_map.get(style_preset or "None", "")
    if style_suffix:
        final_prompt = f"{final_prompt}, {style_suffix}".strip(", ")

    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "input": {
            "task": task,
            "model": model_name,
            "prompt": final_prompt,
            "negative_prompt": neg_prompt,
            "width": int(width) if width else 1024,
            "height": int(height) if height else 1024,
            "steps": int(steps) if steps else 30,
            "guidance_scale": float(cfg) if cfg else 7.5,
            "seed": int(seed) if seed else 42,
            "upscaler": upscaler,
            "style_preset": style_preset or "None",
            "lora": lora_name or "None",
            "lora_weight": float(lora_strength) if lora_strength is not None else 0.75
        }
    }

    if quality_grade:
        payload["input"]["quality_grade"] = quality_grade
    if aspect_ratio_label:
        payload["input"]["aspect_ratio"] = aspect_ratio_label

    if init_image is not None:
        buffered = io.BytesIO()
        init_image.save(buffered, format="PNG")
        payload["input"]["init_image"] = base64.b64encode(buffered.getvalue()).decode("utf-8")

    try:
        response = requests.post(RUNPOD_ENDPOINT, json=payload, headers=headers, timeout=180)
        res_json = response.json()

        if "output" in res_json:
            output = res_json["output"]
            if isinstance(output, dict) and "image" in output:
                img_bytes = base64.b64decode(output["image"])
                return Image.open(io.BytesIO(img_bytes))
        return None
    except Exception as e:
        print(f"Connection Error to RunPod: {str(e)}")
        return None

def generate_multi_input_task(
    prompt,
    neg_prompt,
    width,
    height,
    steps,
    cfg,
    seed,
    model_name,
    task,
    img1,
    img2,
    img3,
    upscaler,
    lora_name="None",
    lora_strength=0.75,
    quality_grade=None,
    aspect_ratio_label=None
):
    composite_img = auto_composite_dynamic_grid(img1, img2, img3)
    return generate_image(
        prompt=prompt,
        neg_prompt=neg_prompt,
        width=width,
        height=height,
        steps=steps,
        cfg=cfg,
        seed=seed,
        model_name=model_name,
        task=task,
        init_image=composite_img,
        upscaler=upscaler,
        style_preset="None",
        lora_name=lora_name,
        lora_strength=lora_strength,
        quality_grade=quality_grade,
        aspect_ratio_label=aspect_ratio_label
    )

master_prompt_choices = []
master_prompt_dict = {}
if MASTER_PROMPTS:
    for k, v in MASTER_PROMPTS.items():
        title = v.get("title", f"Prompt {k}")
        desc = v.get("description", "")
        choice_label = f"{k}. {title}"
        master_prompt_choices.append(choice_label)
        master_prompt_dict[choice_label] = desc
else:
    master_prompt_choices = ["1. Default Cinematic Shot"]
    master_prompt_dict["1. Default Cinematic Shot"] = "A cinematic futuristic scene with dramatic lighting."

def load_master_prompt_desc(selected_choice):
    return master_prompt_dict.get(selected_choice, "")

quick_retouch_choices = []
quick_retouch_dict = {}
if QUICK_RETOUCH_SLASH_COMMANDS:
    for idx, (k, v) in enumerate(QUICK_RETOUCH_SLASH_COMMANDS.items(), 1):
        choice_label = f"{idx}. {k}"
        quick_retouch_choices.append(choice_label)
        quick_retouch_dict[choice_label] = v
else:
    quick_retouch_choices = ["1. /RESTORE"]
    quick_retouch_dict["1. /RESTORE"] = "Restore old or blurry photo into high definition crisp quality"

def handle_image_slash_command(selected_choice):
    return quick_retouch_dict.get(selected_choice, "A high definition professional retouch result.")

cgi_billboard_slash_command_dict = {
    "/3d-billboard-reveal": "3D CGI Billboard illusion, product pops out dynamically from giant curved outdoor screen, hyper-realistic urban environment",
    "/ugc-product-hook": "Realistic creator holding product in natural lighting, dynamic motion, highly detailed commercial advertisement style"
}

def handle_cgi_slash_command(command_key):
    return cgi_billboard_slash_command_dict.get(command_key, "3D CGI Billboard commercial advertisement shot.")

# Professional English Contextual Chatbot Response Function
def chat_bot_response(message, history):
    if not message:
        return history, ""

    msg_lower = message.lower()

    if "puja" in msg_lower or "durga" in msg_lower or "festival" in msg_lower:
        bot_reply = "For editing Durga Puja or festive pictures, you can use our 'Presets 🎨' tab or 'Retouch ⚡' tab which features various festive templates and professional master prompts."
    elif "cinematic" in msg_lower or "video" in msg_lower or "animation" in msg_lower:
        bot_reply = "For cinematic videos and animations, please check out our 'Cinematic 🎥' and 'Img ➔ Anim 🎞️' tabs to easily generate high-definition motion outputs."
    elif "image to image" in msg_lower or "i2i" in msg_lower or "photo" in msg_lower or "edit" in msg_lower:
        bot_reply = "For image-to-image transformations and photo editing, navigate to the 'Img ➔ Img' or 'Retouch ⚡' tab, upload your reference image, and enter your creative prompt."
    else:
        bot_reply = f"Welcome to AccPixelForge! Regarding your query ('{message}'), you can explore our various creative studio tabs (Text->Img, Flow, Billboard, Face Swap) above. How would you like to proceed?"

    history = history + [{"role": "user", "content": message}, {"role": "assistant", "content": bot_reply}]
    return history, ""

# Base64 Direct Background Injection
bg_css_value = f'data:image/png;base64,{bg_b64}' if bg_b64 else 'https://huggingface.co/spaces/Arnab1989/AccPixelForge/resolve/main/bg.png'

custom_css = f"""
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;900&family=Poppins:wght@300;400;500;600;700&display=swap');

html, body {{
    background: url("{bg_css_value}") no-repeat center top fixed !important;
    background-size: 100% 100% !important;
    background-color: #000000 !important;
    min-height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
}}

.gradio-container, gradio-app, .main, .contain, .app, div[class*="gradio"] {{
    background: transparent !important;
    background-color: transparent !important;
    color: #ffffff !important;
    font-family: 'Poppins', sans-serif !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    filter: none !important;
    padding-top: 5px !important;
}}

header, footer, #footer, .footer, .built-with, div[class*="footer"],
.gradio-container > footer, .gradio-container > header, div[class*="header"],
button[aria-label*="theme"], button[title*="theme"], .theme-toggle,
.svelte-1ipelgc, .svelte-1g7vh8a, a[href*="huggingface"], iframe[src*="huggingface"],
div[class*="space-status"], div[class*="runtime-status"],
button.overflow-dropdown-btn, .tab-nav .overflow-menu, button[aria-label*="More"] {{
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}

div[role="tablist"], .tab-nav {{
    display: flex !important;
    flex-wrap: nowrap !important;
    gap: 3px !important;
    border-bottom: 2px solid rgba(56, 189, 248, 0.8) !important;
    padding-bottom: 6px !important;
    justify-content: space-between !important;
    width: 100% !important;
    overflow-x: auto !important;
    background: rgba(5, 2, 20, 0.45) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(4px) !important;
}}

button[role="tab"] {{
    flex: 1 1 auto !important;
    white-space: nowrap !important;
    text-align: center !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.9), 0 0 8px rgba(56, 189, 248, 0.6) !important;
    background: rgba(10, 5, 30, 0.55) !important;
    border: 1px solid rgba(56, 189, 248, 0.5) !important;
    border-radius: 8px !important;
    padding: 6px 6px !important;
    font-size: 11px !important;
    min-height: 38px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    letter-spacing: 0.3px !important;
}}

button[role="tab"][aria-selected="true"], button[role="tab"].selected {{
    color: #ffffff !important;
    background: linear-gradient(135deg, rgba(2, 132, 199, 0.95) 0%, rgba(124, 58, 237, 0.95) 100%) !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 20px rgba(56, 189, 248, 0.9) !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.9) !important;
}}

label, span[data-testid="block-info"], .label-wrap {{
    background-color: transparent !important;
    color: #38bdf8 !important;
    font-weight: 700 !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.8) !important;
    border: none !important;
}}

/* Radio buttons fix: make labels and radio circles clearly interactive & visible */
div[data-testid="radio-group"] label,
.gr-radio label {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    cursor: pointer !important;
    pointer-events: auto !important;
    color: #ffffff !important;
    background: rgba(10, 15, 35, 0.72) !important;
    border: 1px solid rgba(56, 189, 248, 0.45) !important;
    border-radius: 8px !important;
    padding: 6px 10px !important;
    margin: 2px !important;
    user-select: none !important;
    position: relative !important;
    z-index: 5 !important;
}}

div[data-testid="radio-group"] input[type="radio"],
.gr-radio input[type="radio"] {{
    accent-color: #38bdf8 !important;
    width: 16px !important;
    height: 16px !important;
    cursor: pointer !important;
    pointer-events: auto !important;
    opacity: 1 !important;
    position: relative !important;
    z-index: 6 !important;
}}

div[data-testid="radio-group"] label:has(input:checked),
.gr-radio label:has(input:checked) {{
    background: linear-gradient(135deg, rgba(2, 132, 199, 0.9) 0%, rgba(124, 58, 237, 0.9) 100%) !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 12px rgba(56, 189, 248, 0.65) !important;
}}

.panel, .form, .gr-box, .gr-panel, .block, .gr-block, .tabitem, .accordion, fieldset {{
    background: transparent !important;
    background-color: transparent !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    filter: none !important;
    border: 1px solid rgba(56, 189, 248, 0.4) !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    box-shadow: none !important;
}}

input[type="text"], input[type="number"], textarea, select, .gr-input, .gr-text-input, div[data-testid="dropdown"], button, .gr-button {{
    background: rgba(5, 2, 20, 0.45) !important;
    color: #ffffff !important;
    border: 1px solid rgba(56, 189, 248, 0.5) !important;
    border-radius: 10px !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
}}

button:hover, .gr-button:hover {{
    background: linear-gradient(135deg, rgba(2, 132, 199, 0.9) 0%, rgba(219, 39, 119, 0.9) 100%) !important;
    border-color: #38bdf8 !important;
    color: #ffffff !important;
    box-shadow: 0 0 20px rgba(56, 189, 248, 0.9) !important;
}}

.glowing-header {{
    color: #7dd3fc !important;
    font-weight: 700 !important;
    text-shadow: 0 0 10px rgba(56, 189, 248, 0.8);
}}
"""

custom_js = f"""
function() {{
    const killStyle = document.createElement('style');
    killStyle.innerHTML = `
        header, footer, #footer, .footer, .built-with {{
            display: none !important;
        }}
        .tab-nav button.overflow-dropdown-btn, .tab-nav > .overflow-menu, button[aria-label*="More"] {{
            display: none !important;
        }}
    `;
    document.head.appendChild(killStyle);

    const favUri = "{favicon_data_uri}";
    if (favUri) {{
        let links = document.querySelectorAll('link[rel*="icon"]');
        if (links.length === 0) {{
            const link = document.createElement('link');
            link.rel = 'icon';
            link.type = 'image/png';
            link.href = favUri;
            document.head.appendChild(link);
        }} else {{
            links.forEach(el => {{
                el.type = 'image/png';
                el.href = favUri;
            }});
        }}
    }}
}}
"""

with gr.Blocks(title="AccPixelForge", css=custom_css, js=custom_js, head=favicon_head_html) as demo:

    gr.HTML(f"""
    <div style="display: flex; align-items: center; padding: 8px 15px; background: rgba(5, 2, 20, 0.25); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 12px; margin-bottom: 12px;">
        {logo_element}
        <span style="font-size: 16px; font-weight: 700; color: #38bdf8; text-shadow: 0 0 10px rgba(56, 189, 248, 0.8);">| AI Creative Studio</span>
    </div>
    """)

    with gr.Row():
        checkpoint_model = gr.Dropdown(
            choices=checkpoint_models_list,
            value=checkpoint_models_list[0],
            label="🤖 Select Checkpoint Model",
            interactive=True,
            scale=2
        )
        lora_model = gr.Dropdown(
            choices=lora_models_list,
            value="None",
            label="✨ Select LoRA Enhancement",
            interactive=True,
            scale=1
        )
        lora_weight = gr.Slider(
            minimum=0.0,
            maximum=1.5,
            value=0.75,
            step=0.05,
            label="🎯 LoRA Weight/Strength",
            interactive=True,
            scale=1
        )

    with gr.Tabs():
        # 1. Text-to-Image Tab
        with gr.TabItem("Text ➔ Img"):
            with gr.Row():
                with gr.Column(scale=1):
                    prompt = gr.Textbox(
                        label="✍ Main Prompt",
                        placeholder="Describe your vision...",
                        lines=3,
                        interactive=True
                    )
                    with gr.Row():
                        t2i_mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Voice-to-Text Input")
                        t2i_trans_btn = gr.Button("🌐 Auto-Translate to English Prompt", scale=2)
                    t2i_mic.stop_recording(fn=mock_transcribe, inputs=t2i_mic, outputs=prompt)
                    t2i_trans_btn.click(fn=auto_translate_prompt, inputs=prompt, outputs=prompt)

                    style_preset = gr.Radio(
                        choices=["None", "Photorealistic", "Cinematic", "Oil Painting", "Anime", "Cyberpunk", "3D Render"],
                        value="None",
                        label="🎨 Art Style Preset",
                        interactive=True
                    )

                    t2i_upscaler = gr.Dropdown(
                        choices=upscaler_models_list,
                        value="None",
                        label="🔍 Select AI Upscaler Engine",
                        interactive=True
                    )

                    with gr.Accordion("📐 Aspect Ratio & Pixel Dimensions", open=True):
                        aspect_ratio = gr.Radio(
                            choices=aspect_ratios_list,
                            value="1:1 (1024x1024 Square)",
                            label="Select Aspect Ratio Preset",
                            interactive=True
                        )
                        with gr.Row():
                            width = gr.Slider(512, 2048, value=1024, step=64, label="Custom Width", interactive=True)
                            height = gr.Slider(512, 2048, value=1024, step=64, label="Custom Height", interactive=True)

                        aspect_ratio.change(
                            fn=update_dimensions_from_preset,
                            inputs=aspect_ratio,
                            outputs=[width, height]
                        )

                    generate_btn = gr.Button("⚡ Generate Creative Image", variant="primary", interactive=True)

                with gr.Column(scale=1):
                    output_image = gr.Image(label="🖼 Generated Output Showcase", interactive=False, type="pil")

            generate_btn.click(
                fn=generate_image,
                inputs=[
                    prompt,
                    gr.State("blurry, low quality, deformed"),
                    width,
                    height,
                    gr.State(30),
                    gr.State(7.5),
                    gr.State(42),
                    checkpoint_model,
                    gr.State("t2i"),
                    gr.State(None),
                    t2i_upscaler,
                    style_preset,
                    lora_model,
                    lora_weight,
                    gr.State(None),
                    aspect_ratio
                ],
                outputs=output_image
            )

        # 2. Quick AI Retouch & Presets Tab
        with gr.TabItem("Retouch ⚡"):
            gr.Markdown('<h3 class="glowing-header">⚡ Quick AI Retouch & Presets [200+ Master Prompts] (Multi-Ref & Auto-Translator)</h3>')

            with gr.Accordion("📂 Multi-Reference Input Slots (3 Slots)", open=True):
                with gr.Row():
                    quick_img_1 = gr.Image(label="🖼️ Slot 1: Primary Image / Subject", type="pil", interactive=True)
                    quick_img_2 = gr.Image(label="🖼️ Slot 2: Reference Image / Background", type="pil", interactive=True)
                    quick_img_3 = gr.Image(label="🖼️ Slot 3: Additional Ref / Asset", type="pil", interactive=True)

            with gr.Row():
                with gr.Column(scale=1):
                    quick_prompt = gr.Textbox(
                        label="✍️ Slash Command / Prompt Box (Auto-Translator Enabled)",
                        placeholder="Type slash command or prompt in any language...",
                        lines=3,
                        interactive=True
                    )

                    with gr.Row():
                        quick_mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Voice-to-Text")
                        quick_translate_btn = gr.Button("🌐 Auto-Translate to English Prompt", scale=2)

                    quick_mic.stop_recording(fn=mock_transcribe, inputs=quick_mic, outputs=quick_prompt)
                    quick_translate_btn.click(fn=auto_translate_prompt, inputs=quick_prompt, outputs=quick_prompt)

                    with gr.Row():
                        quick_slash_select = gr.Dropdown(
                            choices=quick_retouch_choices,
                            value=quick_retouch_choices[0] if quick_retouch_choices else None,
                            label="⚡ Quick Slash Command Select [200+ Master Prompts]",
                            interactive=True,
                            scale=2
                        )
                        quick_apply_slash = gr.Button("📥 Insert Slash Prompt", scale=1)
                        quick_apply_slash.click(fn=handle_image_slash_command, inputs=quick_slash_select, outputs=quick_prompt)

                    quick_upscaler = gr.Dropdown(
                        choices=upscaler_models_list,
                        value="None",
                        label="🔍 Select AI Upscaler Engine",
                        interactive=True
                    )

                    quick_btn = gr.Button("⚡ Run Quick Retouch & Preset", variant="primary", interactive=True)

                with gr.Column(scale=1):
                    quick_output = gr.Image(label="✨ Quick Retouch Generated Output", interactive=False, type="pil")

            quick_btn.click(
                fn=generate_multi_input_task,
                inputs=[
                    quick_prompt,
                    gr.State("blurry, low quality, deformed"),
                    gr.State(1024),
                    gr.State(1024),
                    gr.State(30),
                    gr.State(7.5),
                    gr.State(42),
                    checkpoint_model,
                    gr.State("quick_retouch"),
                    quick_img_1,
                    quick_img_2,
                    quick_img_3,
                    quick_upscaler,
                    lora_model,
                    lora_weight
                ],
                outputs=quick_output
            )

        # 3. Dynamic Flow AI & Master Prompts Tab
        with gr.TabItem("Flow ⭐"):
            gr.Markdown('<h3 class="glowing-header">🔥 Dynamic Flow AI & Master Prompts Library (Auto-Translator & Multi-Input)</h3>')

            with gr.Accordion("📂 Multi-Input Image Slots (1 to 3 Slots)", open=True):
                with gr.Row():
                    dyn_img_1 = gr.Image(label="🖼️ Slot 1: Primary Subject / Photo", type="pil", interactive=True)
                    dyn_img_2 = gr.Image(label="🖼️ Slot 2: Background / Secondary Reference", type="pil", interactive=True)
                    dyn_img_3 = gr.Image(label="🖼️ Slot 3: Accessory / Extra Reference", type="pil", interactive=True)

            with gr.Row():
                with gr.Column(scale=1):
                    master_dropdown = gr.Dropdown(
                        choices=master_prompt_choices,
                        value=master_prompt_choices[0] if master_prompt_choices else None,
                        label="📚 Select Master Prompt Category / Item [200+ Master Prompts] ⚡",
                        interactive=True
                    )

                    master_desc_box = gr.Textbox(
                        label="📄 Prompt Description",
                        value=load_master_prompt_desc(master_prompt_choices[0]) if master_prompt_choices else "",
                        lines=5,
                        interactive=True
                    )

                    with gr.Row():
                        master_mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Voice-to-Text")
                        dyn_translate_btn = gr.Button("🌐 Auto-Translate to English Prompt", scale=2)

                    master_mic.stop_recording(fn=mock_transcribe, inputs=master_mic, outputs=master_desc_box)
                    dyn_translate_btn.click(fn=auto_translate_prompt, inputs=master_desc_box, outputs=master_desc_box)

                    master_dropdown.change(
                        fn=load_master_prompt_desc,
                        inputs=master_dropdown,
                        outputs=master_desc_box
                    )

                    dyn_render_quality = gr.Dropdown(
                        choices=video_render_quality_list,
                        value=video_render_quality_list[0],
                        label="🎬 Video Render Quality Grade",
                        interactive=True
                    )

                    dyn_generate_btn = gr.Button("⚡ Generate Dynamic Flow Result", variant="primary", interactive=True)

                with gr.Column(scale=1):
                    dyn_output_image = gr.Image(label="✨ Dynamic Flow Generated Output", interactive=False, type="pil")

            dyn_generate_btn.click(
                fn=generate_multi_input_task,
                inputs=[
                    master_desc_box,
                    gr.State("blurry, low quality, deformed"),
                    gr.State(1024),
                    gr.State(1024),
                    gr.State(30),
                    gr.State(7.5),
                    gr.State(42),
                    checkpoint_model,
                    gr.State("dynamic_flow"),
                    dyn_img_1,
                    dyn_img_2,
                    dyn_img_3,
                    gr.State("None"),
                    lora_model,
                    lora_weight,
                    dyn_render_quality
                ],
                outputs=dyn_output_image
            )

        # 4. CGI Billboard Tab
        with gr.TabItem("Billboard ✨"):
            gr.Markdown('<h3 class="glowing-header">🎥 Multi-Asset Storyboard, CGI 3D Billboard & Camera Motion Studio</h3>')

            with gr.Accordion("📂 Multi-Asset Input Slots (6 Slots)", open=True):
                with gr.Row():
                    asset_1 = gr.Image(label="🛍️ Slot 1: Primary Product / Character", type="pil", interactive=True)
                    asset_2 = gr.Image(label="🎁 Slot 2: Secondary Product / Subject", type="pil", interactive=True)
                    asset_3 = gr.Image(label="🌇 Slot 3: Primary Background / Location", type="pil", interactive=True)
                with gr.Row():
                    asset_4 = gr.Image(label="🌄 Slot 4: Secondary Environment / Skybox", type="pil", interactive=True)
                    asset_5 = gr.Image(label="🕶️ Slot 5: Primary Prop / Outfit", type="pil", interactive=True)
                    asset_6 = gr.Image(label="👜 Slot 6: Secondary Prop / Accessory", type="pil", interactive=True)

            with gr.Row():
                with gr.Column(scale=1):
                    df_prompt = gr.Textbox(
                        label="✍️ Prompt / Slash Command Box",
                        placeholder="Type slash command or commercial prompt...",
                        lines=3,
                        interactive=True
                    )
                    with gr.Row():
                        df_mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Voice-to-Text Input")
                        df_trans_btn = gr.Button("🌐 Auto-Translate to English Prompt", scale=2)
                    df_mic.stop_recording(fn=mock_transcribe, inputs=df_mic, outputs=df_prompt)
                    df_trans_btn.click(fn=auto_translate_prompt, inputs=df_prompt, outputs=df_prompt)

                    with gr.Row():
                        cgi_slash_select = gr.Dropdown(
                            choices=list(cgi_billboard_slash_command_dict.keys()),
                            value="/3d-billboard-reveal",
                            label="⚡ Commercial Billboard Slash Command Select",
                            interactive=True,
                            scale=2
                        )
                        cgi_apply_slash = gr.Button("📥 Insert Slash Prompt", scale=1)
                        cgi_apply_slash.click(fn=handle_cgi_slash_command, inputs=cgi_slash_select, outputs=df_prompt)

                    df_model_engine = gr.Dropdown(
                        choices=video_render_quality_list,
                        value=video_render_quality_list[0],
                        label="🎬 Video Render Quality Grade",
                        interactive=True
                    )

                    df_btn = gr.Button("🚀 Generate 6-Slot Multi-Asset Storyboard Video", variant="primary", interactive=True)

                with gr.Column(scale=1):
                    preview_grid_box = gr.Image(label="🖼️ 6-Slot Auto-Generated Storyboard / Billboard Grid Preview", interactive=False, type="pil")
                    df_output = gr.Video(label="🎥 Generated Dynamic Motion Video Output", interactive=False)

                    for asset in [asset_1, asset_2, asset_3, asset_4, asset_5, asset_6]:
                        asset.change(
                            fn=auto_composite_storyboard_grid,
                            inputs=[asset_1, asset_2, asset_3, asset_4, asset_5, asset_6],
                            outputs=preview_grid_box
                        )

            df_btn.click(
                fn=generate_image,
                inputs=[
                    df_prompt,
                    gr.State("blurry, low quality, deformed"),
                    gr.State(1024),
                    gr.State(1024),
                    gr.State(25),
                    gr.State(7.5),
                    gr.State(42),
                    checkpoint_model,
                    gr.State("cgi_billboard"),
                    preview_grid_box,
                    gr.State("None"),
                    gr.State("None"),
                    lora_model,
                    lora_weight,
                    df_model_engine
                ],
                outputs=df_output
            )

        # 5. Cinematic Studio Tab
        with gr.TabItem("Cinematic 🎥"):
            gr.Markdown('<h3 class="glowing-header">🎥 Masterpiece High-Definition Cinematic Video Generator</h3>')

            with gr.Accordion("📂 Multi-Reference Input Slots (3 Slots for Image-to-Video)", open=True):
                with gr.Row():
                    cine_img_1 = gr.Image(label="📥 Slot 1: Primary Image / Subject", type="pil", interactive=True)
                    cine_img_2 = gr.Image(label="📥 Slot 2: Reference Image / Background", type="pil", interactive=True)
                    cine_img_3 = gr.Image(label="📥 Slot 3: Additional Ref / Asset", type="pil", interactive=True)

            with gr.Row():
                with gr.Column(scale=1):
                    cinematic_prompt = gr.Textbox(
                        label="🎞 Cinematic Motion Description",
                        placeholder="Type any creative vision...",
                        lines=3,
                        interactive=True
                    )
                    with gr.Row():
                        cine_mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Voice-to-Text Input")
                        cine_trans_btn = gr.Button("🌐 Auto-Translate to English Prompt", scale=2)
                    cine_mic.stop_recording(fn=mock_transcribe, inputs=cine_mic, outputs=cinematic_prompt)
                    cine_trans_btn.click(fn=auto_translate_prompt, inputs=cinematic_prompt, outputs=cinematic_prompt)

                    cine_quality = gr.Dropdown(
                        choices=video_render_quality_list,
                        value=video_render_quality_list[0],
                        label="🎬 Video Render Quality Grade",
                        interactive=True
                    )

                    cine_aspect = gr.Dropdown(
                        choices=video_aspect_ratios_list,
                        value=video_aspect_ratios_list[0],
                        label="📐 Select Video Aspect Ratio",
                        interactive=True
                    )

                    cinematic_btn = gr.Button("🚀 Generate Cinematic Video", variant="primary", interactive=True)
                with gr.Column(scale=1):
                    cine_preview_grid = gr.Image(label="🖼️ Auto-Generated Multi-Reference Grid Preview", interactive=False, type="pil")
                    cinematic_output = gr.Video(label="🎥 Generated Cinematic Video Output", interactive=False)

                    for asset in [cine_img_1, cine_img_2, cine_img_3]:
                        asset.change(
                            fn=auto_composite_dynamic_grid,
                            inputs=[cine_img_1, cine_img_2, cine_img_3],
                            outputs=cine_preview_grid
                        )

            cinematic_btn.click(
                fn=generate_multi_input_task,
                inputs=[
                    cinematic_prompt,
                    gr.State("blurry, low quality, deformed"),
                    gr.State(1280),
                    gr.State(720),
                    gr.State(25),
                    gr.State(7.5),
                    gr.State(42),
                    checkpoint_model,
                    gr.State("cinematic_video"),
                    cine_img_1,
                    cine_img_2,
                    cine_img_3,
                    gr.State("None"),
                    lora_model,
                    lora_weight,
                    cine_quality,
                    cine_aspect
                ],
                outputs=cinematic_output
            )

        # 6. Image-to-Image Tab
        with gr.TabItem("Img ➔ Img"):
            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Accordion("📂 Multi-Reference Input Slots (3 Slots)", open=True):
                        with gr.Row():
                            i2i_img_1 = gr.Image(label="📥 Slot 1: Primary Input Image", type="pil", interactive=True)
                            i2i_img_2 = gr.Image(label="📥 Slot 2: Secondary Ref Image", type="pil", interactive=True)
                            i2i_img_3 = gr.Image(label="📥 Slot 3: Additional Ref Image", type="pil", interactive=True)

                    i2i_prompt = gr.Textbox(label="✍️ Transformation Prompt", placeholder="Describe how to modify the image...", lines=2, interactive=True)
                    with gr.Row():
                        i2i_mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Voice-to-Text Input")
                        i2i_trans_btn = gr.Button("🌐 Auto-Translate to English Prompt", scale=2)
                    i2i_mic.stop_recording(fn=mock_transcribe, inputs=i2i_mic, outputs=i2i_prompt)
                    i2i_trans_btn.click(fn=auto_translate_prompt, inputs=i2i_prompt, outputs=i2i_prompt)

                    i2i_upscaler = gr.Dropdown(
                        choices=upscaler_models_list,
                        value="None",
                        label="🔍 Select AI Upscaler Engine",
                        interactive=True
                    )

                    i2i_btn = gr.Button("🔄 Transform Image", variant="primary", interactive=True)
                with gr.Column(scale=1):
                    i2i_output = gr.Image(label="✨ Transformed Output", interactive=False, type="pil")

            i2i_btn.click(
                fn=generate_multi_input_task,
                inputs=[
                    i2i_prompt,
                    gr.State("blurry, low quality, deformed"),
                    gr.State(1024),
                    gr.State(1024),
                    gr.State(30),
                    gr.State(7.5),
                    gr.State(42),
                    checkpoint_model,
                    gr.State("i2i"),
                    i2i_img_1,
                    i2i_img_2,
                    i2i_img_3,
                    i2i_upscaler,
                    lora_model,
                    lora_weight
                ],
                outputs=i2i_output
            )

        # 7. Image-to-Animation Tab
        with gr.TabItem("Img ➔ Anim 🎞️"):
            with gr.Row():
                with gr.Column(scale=1):
                    anim_input_image = gr.Image(label="📥 Upload Static Image for Animation", type="pil", interactive=True)
                    anim_prompt = gr.Textbox(label="✍️ Animation Motion Prompt", placeholder="Describe the motion...", lines=2, interactive=True)
                    with gr.Row():
                        anim_mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Voice-to-Text Input")
                        anim_trans_btn = gr.Button("🌐 Auto-Translate to English Prompt", scale=2)
                    anim_mic.stop_recording(fn=mock_transcribe, inputs=anim_mic, outputs=anim_prompt)
                    anim_trans_btn.click(fn=auto_translate_prompt, inputs=anim_prompt, outputs=anim_prompt)

                    anim_quality = gr.Dropdown(
                        choices=video_render_quality_list,
                        value=video_render_quality_list[0],
                        label="🎬 Video Render Quality Grade",
                        interactive=True
                    )

                    anim_btn = gr.Button("🎥 Generate Animation Video", variant="primary", interactive=True)
                with gr.Column(scale=1):
                    anim_output = gr.Image(label="🎞 Generated Animation Output", interactive=False, type="pil")

            anim_btn.click(
                fn=generate_image,
                inputs=[
                    anim_prompt,
                    gr.State("blurry, low quality, deformed"),
                    gr.State(1024),
                    gr.State(1024),
                    gr.State(25),
                    gr.State(7.5),
                    gr.State(42),
                    checkpoint_model,
                    gr.State("animation"),
                    anim_input_image,
                    gr.State("None"),
                    gr.State("None"),
                    lora_model,
                    lora_weight,
                    anim_quality
                ],
                outputs=anim_output
            )

        # 8. Face Swapping & Consistency Tool Tab
        with gr.TabItem("Face Swap 🎭"):
            gr.Markdown('<h3 class="glowing-header">🎭 Face Swapping & Character Consistency Tool</h3>')
            with gr.Row():
                with gr.Column(scale=1):
                    face_source_img = gr.Image(label="👤 Source Face / Character Reference", type="pil", interactive=True)
                    face_target_img = gr.Image(label="🖼️ Target Portrait / Scene Image", type="pil", interactive=True)
                    face_prompt = gr.Textbox(label="✍️ Custom Blending Prompt", value="Seamless face swap, realistic lighting and skin tone matching", lines=2, interactive=True)
                    with gr.Row():
                        face_mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Voice-to-Text Input")
                        face_trans_btn = gr.Button("🌐 Auto-Translate to English Prompt", scale=2)
                    face_mic.stop_recording(fn=mock_transcribe, inputs=face_mic, outputs=face_prompt)
                    face_trans_btn.click(fn=auto_translate_prompt, inputs=face_prompt, outputs=face_prompt)

                    face_upscaler = gr.Dropdown(
                        choices=upscaler_models_list,
                        value="None",
                        label="🔍 Select AI Upscaler Engine",
                        interactive=True
                    )

                    face_swap_btn = gr.Button("🔄 Execute Face Swap & Consistency", variant="primary", interactive=True)
                with gr.Column(scale=1):
                    face_output_img = gr.Image(label="✨ Consistent Face Swapped Output", interactive=False, type="pil")

            face_swap_btn.click(
                fn=generate_multi_input_task,
                inputs=[
                    face_prompt,
                    gr.State("blurry"),
                    gr.State(1024),
                    gr.State(1024),
                    gr.State(30),
                    gr.State(7.5),
                    gr.State(42),
                    checkpoint_model,
                    gr.State("i2i"),
                    face_source_img,
                    face_target_img,
                    gr.State(None),
                    face_upscaler,
                    lora_model,
                    lora_weight
                ],
                outputs=face_output_img
            )

        # 9. AI Background Remover & Eraser Tab
        with gr.TabItem("Bg Eraser ✂️"):
            gr.Markdown('<h3 class="glowing-header">✂️ AI Background Remover & Object Eraser (One-Click Clean Tool)</h3>')
            with gr.Row():
                with gr.Column(scale=1):
                    bg_input_img = gr.Image(label="📥 Upload Image to Remove Background", type="pil", interactive=True)
                    bg_prompt = gr.Textbox(label="✍️ Custom Instructions (Optional)", value="Remove background, transparent white isolated, high quality", lines=2, interactive=True)
                    with gr.Row():
                        bg_mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Voice-to-Text Input")
                        bg_trans_btn = gr.Button("🌐 Auto-Translate to English Prompt", scale=2)
                    bg_mic.stop_recording(fn=mock_transcribe, inputs=bg_mic, outputs=bg_prompt)
                    bg_trans_btn.click(fn=auto_translate_prompt, inputs=bg_prompt, outputs=bg_prompt)

                    bg_upscaler = gr.Dropdown(
                        choices=upscaler_models_list,
                        value="None",
                        label="🔍 Select AI Upscaler Engine",
                        interactive=True
                    )

                    bg_remove_btn = gr.Button("🚀 Remove Background Instantly", variant="primary", interactive=True)
                with gr.Column(scale=1):
                    bg_output_img = gr.Image(label="✨ Background Removed Output", interactive=False, type="pil")

            bg_remove_btn.click(
                fn=generate_image,
                inputs=[
                    bg_prompt,
                    gr.State("blurry"),
                    gr.State(1024),
                    gr.State(1024),
                    gr.State(20),
                    gr.State(7.5),
                    gr.State(42),
                    checkpoint_model,
                    gr.State("i2i"),
                    bg_input_img,
                    bg_upscaler,
                    gr.State("None"),
                    lora_model,
                    lora_weight
                ],
                outputs=bg_output_img
            )

        # 10. Preset Template Gallery Tab
        with gr.TabItem("Presets 🎨"):
            gr.Markdown('<h3 class="glowing-header">🎨 Visual Preset Template Gallery (35+ Presets with 3-Slot Reference Upload)</h3>')

            with gr.Accordion("📂 Multi-Reference Input Slots for Presets (3 Slots)", open=True):
                with gr.Row():
                    preset_img_1 = gr.Image(label="🖼️ Slot 1: Primary Subject / Photo", type="pil", interactive=True)
                    preset_img_2 = gr.Image(label="🖼️ Slot 2: Background / Reference", type="pil", interactive=True)
                    preset_img_3 = gr.Image(label="🖼️ Slot 3: Accessory / Extra Asset", type="pil", interactive=True)

            with gr.Row():
                with gr.Column(scale=1):
                    preset_select_dropdown = gr.Dropdown(
                        choices=list(PRESET_TEMPLATES_DB.keys()),
                        value=list(PRESET_TEMPLATES_DB.keys())[0] if PRESET_TEMPLATES_DB else "1. Cyberpunk Sci-Fi Pod",
                        label="🌟 Choose Visual Preset Style Card (35+ Styles)",
                        interactive=True
                    )
                    preset_preview_text = gr.Textbox(
                        label="📝 Selected Template Prompt Preview",
                        value=load_preset_template(list(PRESET_TEMPLATES_DB.keys())[0]) if PRESET_TEMPLATES_DB else "",
                        lines=3,
                        interactive=True
                    )
                    with gr.Row():
                        preset_mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Voice-to-Text Input")
                        preset_trans_btn = gr.Button("🌐 Auto-Translate to English Prompt", scale=2)
                    preset_mic.stop_recording(fn=mock_transcribe, inputs=preset_mic, outputs=preset_preview_text)
                    preset_trans_btn.click(fn=auto_translate_prompt, inputs=preset_preview_text, outputs=preset_preview_text)

                    preset_upscaler = gr.Dropdown(
                        choices=upscaler_models_list,
                        value="None",
                        label="🔍 Select AI Upscaler Engine",
                        interactive=True
                    )

                    preset_select_dropdown.change(fn=load_preset_template, inputs=preset_select_dropdown, outputs=preset_preview_text)

                    preset_load_btn = gr.Button("🚀 Generate Image from Preset", variant="primary", interactive=True)
                with gr.Column(scale=1):
                    preset_output_img = gr.Image(label="✨ Preset Template Output Showcase", interactive=False, type="pil")

            preset_load_btn.click(
                fn=generate_multi_input_task,
                inputs=[
                    preset_preview_text,
                    gr.State("blurry, low quality"),
                    gr.State(1024),
                    gr.State(1024),
                    gr.State(30),
                    gr.State(7.5),
                    gr.State(42),
                    checkpoint_model,
                    gr.State("preset_flow"),
                    preset_img_1,
                    preset_img_2,
                    preset_img_3,
                    preset_upscaler,
                    lora_model,
                    lora_weight
                ],
                outputs=preset_output_img
            )

        # 11. Prompt Generator Tab
        with gr.TabItem("Prompts G 💡"):
            gr.Markdown('<h3 class="glowing-header">💡 AI-Powered Professional Prompt Builder & Enhancer</h3>')
            with gr.Row():
                with gr.Column(scale=1):
                    base_idea = gr.Textbox(label="🎯 Enter Your Basic Concept", lines=2, interactive=True)
                    with gr.Row():
                        pg_mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙 Voice-to-Text Input")
                        pg_trans_btn = gr.Button("🌐 Auto-Translate to English Prompt", scale=2)
                    pg_mic.stop_recording(fn=mock_transcribe, inputs=pg_mic, outputs=base_idea)
                    pg_trans_btn.click(fn=auto_translate_prompt, inputs=base_idea, outputs=base_idea)

                    enhance_btn = gr.Button("✨ Enhance & Generate Advanced Prompt", variant="primary", interactive=True)
                with gr.Column(scale=1):
                    enhanced_prompt_output = gr.Textbox(label="📝 Optimized AI Prompt Result", lines=4, interactive=False)

            enhance_btn.click(
                fn=lambda x: f"Masterpiece, highly detailed 8k cinematic shot of {x}, professional lighting, dramatic composition",
                inputs=base_idea,
                outputs=enhanced_prompt_output
            )

        # 12. AI Chatbot Tab (Professional English Assistant)
        with gr.TabItem("Chatbot 💬"):
            gr.Markdown('<h3 class="glowing-header">💬 AI Creative Assistant Live Chat</h3>')
            with gr.Column():
                chatbot_view = gr.Chatbot(label="💬 AI Creative Assistant Chat", type="messages", height=400)

                with gr.Row():
                    chat_msg = gr.Textbox(label="Type your message...", placeholder="Ask anything...", scale=4, container=False)
                    chat_send_btn = gr.Button("Send Message 🚀", variant="primary", scale=1)

                with gr.Row():
                    chat_mic = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Voice-to-Text Input", scale=2)
                    chat_trans_btn = gr.Button("🌐 Auto-Translate to English Prompt", scale=3)

                chat_mic.stop_recording(fn=mock_transcribe, inputs=chat_mic, outputs=chat_msg)
                chat_trans_btn.click(fn=auto_translate_prompt, inputs=chat_msg, outputs=chat_msg)

                chat_send_btn.click(
                    fn=chat_bot_response,
                    inputs=[chat_msg, chatbot_view],
                    outputs=[chatbot_view, chat_msg]
                )
                chat_msg.submit(
                    fn=chat_bot_response,
                    inputs=[chat_msg, chatbot_view],
                    outputs=[chatbot_view, chat_msg]
                )

if __name__ == "__main__":
    server_port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=server_port, favicon_path=favicon_path)
