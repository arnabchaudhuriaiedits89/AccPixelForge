import os
import io
import base64
from typing import Optional, List
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from PIL import Image
import requests
import uvicorn

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

app = FastAPI(title="AccPixelForge")

logo_path = "final_logo.png" if os.path.exists("final_logo.png") else None
favicon_path = "favicon.png" if os.path.exists("favicon.png") else logo_path


def get_base64(file_path: Optional[str]) -> str:
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

checkpoint_models_list = [
    "epicrealismXL_pureFix.safetensors",
    "cyberrealisticXL_v100_pruned_fp16.safetensors",
    "RealVisXL_V4.0.safetensors",
    "realvisxlV50_v50LightningBakedvae_full_fp16.safetensors"
]

lora_models_list = [
    "None",
    "epicRealismXL-KiSSEnhancer_Lora.safetensors"
]

upscaler_models_list = [
    "None",
    "RealESRGAN_x4plus.pth",
    "4x-UltraSharp.pth",
    "codeformer.pth"
]

video_render_quality_list = [
    "720p Standard HD (Fast Processing)",
    "1080p Full HD (Film Grade Render)",
    "4K Ultra Cinematic (Masterpiece Resolution)"
]

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

style_presets_list = [
    "None",
    "Photorealistic",
    "Cinematic",
    "Oil Painting",
    "Anime",
    "Cyberpunk",
    "3D Render"
]

art_style_suffix_map = {
    "None": "",
    "Photorealistic": "photorealistic, ultra detailed photography, natural lighting, 8k",
    "Cinematic": "cinematic film still, dramatic lighting, anamorphic lens, 8k",
    "Oil Painting": "rich oil painting on canvas, visible brush strokes, fine art",
    "Anime": "high quality anime illustration, vibrant colors, crisp linework",
    "Cyberpunk": "cyberpunk futuristic neon aesthetic, moody sci-fi lighting, 8k",
    "3D Render": "3d render, octane render, unreal engine 5, studio lighting"
}

cgi_billboard_slash_command_dict = {
    "/3d-billboard-reveal": "3D CGI Billboard illusion, product pops out dynamically from giant curved outdoor screen, hyper-realistic urban environment",
    "/ugc-product-hook": "Realistic creator holding product in natural lighting, dynamic motion, highly detailed commercial advertisement style"
}


def decode_base64_image(data_str: Optional[str]) -> Optional[Image.Image]:
    if not data_str:
        return None
    try:
        if "," in data_str:
            data_str = data_str.split(",", 1)[1]
        img_bytes = base64.b64decode(data_str)
        return Image.open(io.BytesIO(img_bytes))
    except Exception:
        return None


def encode_pil_image(img: Image.Image) -> str:
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode("utf-8")


def build_grid(images: List[Optional[Image.Image]], cell_size: tuple) -> Optional[Image.Image]:
    valid_imgs = [img for img in images if img is not None]
    if not valid_imgs:
        return None

    resized_imgs = [img.convert("RGB").resize(cell_size) for img in valid_imgs]
    cols = min(len(resized_imgs), 3)
    rows = (len(resized_imgs) + cols - 1) // cols

    grid_w = cols * cell_size[0]
    grid_h = rows * cell_size[1]

    grid_image = Image.new("RGB", (grid_w, grid_h), (15, 23, 42))
    for idx, img in enumerate(resized_imgs):
        r = idx // cols
        c = idx % cols
        grid_image.paste(img, (c * cell_size[0], r * cell_size[1]))

    return grid_image


def call_runpod_api(
    prompt: str,
    neg_prompt: str = "blurry, low quality, deformed",
    width: int = 1024,
    height: int = 1024,
    steps: int = 30,
    cfg: float = 7.5,
    seed: int = 42,
    model_name: str = "epicrealismXL_pureFix.safetensors",
    task: str = "t2i",
    init_image: Optional[Image.Image] = None,
    upscaler: str = "None",
    style_preset: str = "None",
    lora_name: str = "None",
    lora_strength: float = 0.75,
    quality_grade: Optional[str] = None,
    aspect_ratio_label: Optional[str] = None
) -> dict:
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

        if "output" in res_json and isinstance(res_json["output"], dict):
            output = res_json["output"]
            if "image" in output and output["image"]:
                img_b64 = output["image"]
                if not img_b64.startswith("data:"):
                    img_b64 = "data:image/png;base64," + img_b64
                return {"ok": True, "type": "image", "data": img_b64}
            if "video" in output and output["video"]:
                vid_val = output["video"]
                if isinstance(vid_val, str) and not vid_val.startswith(("http://", "https://", "data:")):
                    vid_val = "data:video/mp4;base64," + vid_val
                return {"ok": True, "type": "video", "data": vid_val}

        return {"ok": False, "error": "No output returned from RunPod endpoint.", "raw": res_json}
    except Exception as e:
        return {"ok": False, "error": f"Connection Error to RunPod: {str(e)}"}


@app.get("/api/config")
async def get_ui_config():
    master_prompts_list = []
    if MASTER_PROMPTS:
        for k, v in MASTER_PROMPTS.items():
            title = v.get("title", f"Prompt {k}")
            desc = v.get("description", "")
            master_prompts_list.append({"label": f"{k}. {title}", "desc": desc})
    else:
        master_prompts_list.append({
            "label": "1. Default Cinematic Shot",
            "desc": "A cinematic futuristic scene with dramatic lighting."
        })

    quick_retouch_list = []
    if QUICK_RETOUCH_SLASH_COMMANDS:
        for idx, (k, v) in enumerate(QUICK_RETOUCH_SLASH_COMMANDS.items(), 1):
            quick_retouch_list.append({"label": f"{idx}. {k}", "desc": v})
    else:
        quick_retouch_list.append({
            "label": "1. /RESTORE",
            "desc": "Restore old or blurry photo into high definition crisp quality"
        })

    presets_list = []
    if PRESET_TEMPLATES_DB:
        for k, v in PRESET_TEMPLATES_DB.items():
            presets_list.append({"label": k, "desc": v})
    else:
        presets_list.append({
            "label": "1. Cyberpunk Sci-Fi Pod",
            "desc": "Cinematic masterpiece prompt"
        })

    cgi_slash_list = [
        {"label": k, "desc": v} for k, v in cgi_billboard_slash_command_dict.items()
    ]

    return JSONResponse({
        "logo_b64": logo_b64,
        "favicon_b64": favicon_b64,
        "bg_b64": bg_b64,
        "checkpoints": checkpoint_models_list,
        "loras": lora_models_list,
        "upscalers": upscaler_models_list,
        "video_qualities": video_render_quality_list,
        "video_aspect_ratios": video_aspect_ratios_list,
        "aspect_ratios": aspect_ratios_list,
        "aspect_ratio_dimensions": aspect_ratio_dimensions_map,
        "style_presets": style_presets_list,
        "master_prompts": master_prompts_list,
        "quick_retouch": quick_retouch_list,
        "presets": presets_list,
        "cgi_slash_commands": cgi_slash_list
    })


@app.post("/api/transcribe")
async def transcribe_audio(audio: Optional[UploadFile] = File(None)):
    if not audio:
        return JSONResponse({"text": ""})
    return JSONResponse({
        "text": "A cinematic futuristic city with glowing neon lights and flying cars, highly detailed 8k resolution"
    })


@app.post("/api/translate")
async def translate_prompt(request: Request):
    data = await request.json()
    text = (data.get("text") or "").strip()
    if not text:
        return JSONResponse({"text": ""})
    return JSONResponse({
        "text": f"High quality professional cinematic prompt translated from regional input: {text}, highly detailed masterpiece"
    })


@app.post("/api/enhance-prompt")
async def enhance_prompt(request: Request):
    data = await request.json()
    base_idea = (data.get("text") or "").strip()
    if not base_idea:
        return JSONResponse({"text": ""})
    return JSONResponse({
        "text": f"Masterpiece, highly detailed 8k cinematic shot of {base_idea}, professional lighting, dramatic composition"
    })


@app.post("/api/grid-preview")
async def grid_preview(request: Request):
    data = await request.json()
    images_b64 = data.get("images") or []
    grid_type = data.get("grid_type", "dynamic")
    cell_size = (384, 384) if grid_type == "storyboard" else (512, 512)
    pil_imgs = [decode_base64_image(item) for item in images_b64]
    grid_img = build_grid(pil_imgs, cell_size)
    if not grid_img:
        return JSONResponse({"ok": True, "image": None})
    return JSONResponse({"ok": True, "image": encode_pil_image(grid_img)})


@app.post("/api/generate")
async def generate_endpoint(request: Request):
    data = await request.json()
    task = data.get("task", "t2i")
    grid_mode = data.get("grid_mode", "single")

    pil_images = [decode_base64_image(img_str) for img_str in (data.get("images") or [])]
    if grid_mode == "storyboard":
        init_img = build_grid(pil_images, (384, 384))
    elif grid_mode == "dynamic":
        init_img = build_grid(pil_images, (512, 512))
    else:
        init_img = pil_images[0] if pil_images else None

    result = call_runpod_api(
        prompt=data.get("prompt", ""),
        neg_prompt=data.get("neg_prompt", "blurry, low quality, deformed"),
        width=data.get("width", 1024),
        height=data.get("height", 1024),
        steps=data.get("steps", 30),
        cfg=data.get("cfg", 7.5),
        seed=data.get("seed", 42),
        model_name=data.get("model_name", checkpoint_models_list[0]),
        task=task,
        init_image=init_img,
        upscaler=data.get("upscaler", "None"),
        style_preset=data.get("style_preset", "None"),
        lora_name=data.get("lora_name", "None"),
        lora_strength=data.get("lora_strength", 0.75),
        quality_grade=data.get("quality_grade"),
        aspect_ratio_label=data.get("aspect_ratio_label")
    )
    return JSONResponse(result)


@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    message = (data.get("message") or "").strip()
    if not message:
        return JSONResponse({"reply": ""})

    msg_lower = message.lower()
    if "puja" in msg_lower or "durga" in msg_lower or "festival" in msg_lower:
        bot_reply = "For editing Durga Puja or festive pictures, you can use our 'Presets 🎨' tab or 'Retouch ⚡' tab which features various festive templates and professional master prompts."
    elif "cinematic" in msg_lower or "video" in msg_lower or "animation" in msg_lower:
        bot_reply = "For cinematic videos and animations, please check out our 'Cinematic 🎥' and 'Img ➔ Anim 🎞️' tabs to easily generate high-definition motion outputs."
    elif "image to image" in msg_lower or "i2i" in msg_lower or "photo" in msg_lower or "edit" in msg_lower:
        bot_reply = "For image-to-image transformations and photo editing, navigate to the 'Img ➔ Img' or 'Retouch ⚡' tab, upload your reference image, and enter your creative prompt."
    else:
        bot_reply = f"Welcome to AccPixelForge! Regarding your query ('{message}'), you can explore our various creative studio tabs (Text->Img, Flow, Billboard, Face Swap) above. How would you like to proceed?"

    return JSONResponse({"reply": bot_reply})


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>index.html not found. Please upload index.html to the repository.</h1>", status_code=404)


if __name__ == "__main__":
    server_port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=server_port)
