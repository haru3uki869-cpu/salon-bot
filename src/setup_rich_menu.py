import os
import sys
import json
from dotenv import load_dotenv
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob
)
from linebot.v3.messaging.models import (
    RichMenuRequest,
    RichMenuArea,
    RichMenuBounds,
    RichMenuSize,
    PostbackAction,
    MessageAction,
    URIAction
)
from PIL import Image, ImageDraw, ImageFont

# Load env
load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
if not CHANNEL_ACCESS_TOKEN:
    print("Error: LINE_CHANNEL_ACCESS_TOKEN is not set.")
    sys.exit(1)

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

import requests
from io import BytesIO

def create_rich_menu_image(path):
    # Colors
    color_reserve = '#FF7E67' # Coral
    color_info = '#69D2E7'    # Cyan
    color_phone = '#F4D03F'   # Yellow
    
    # Text Color (Black for high contrast)
    text_color = '#000000'
    
    width = 2500
    height = 843
    img = Image.new('RGB', (width, height), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # Use MacOS System Font (Hiragino Sans) for Japanese support
    # Note: Path might vary by MacOS version
    font_paths = [
        "/System/Library/Fonts/jp/HiraginoSans-W6.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/Library/Fonts/Arial Unicode.ttf" # Fallback with some JP support
    ]
    
    font = None
    for f_path in font_paths:
        if os.path.exists(f_path):
            try:
                font = ImageFont.truetype(f_path, 110, index=0) # Index 0 usually works for ttc
                print(f"✅ Loaded System Font: {f_path}")
                break
            except Exception as e:
                print(f"⚠️ Failed to load {f_path}: {e}")
    
    if font is None:
        print("⚠️ All Japanese fonts failed. Trying generic English font (will show tofu for JP).")
        try:
             # Fallback to another common path
            font_path = "/Library/Fonts/Arial.ttf"
            font = ImageFont.truetype(font_path, 110)
        except:
            print("⚠️ All fonts failed. Using default (very small).")
            font = ImageFont.load_default()

    # Define Areas

    # Text labels (Japanese)
    areas = [
        {"rect": [(0, 0), (width//3, height)], "color": color_reserve, "text": "予約\nReserve"},
        {"rect": [(width//3, 0), (width*2//3, height)], "color": color_info, "text": "キャンセル\nCancel"},
        {"rect": [(width*2//3, 0), (width, height)], "color": color_phone, "text": "電話\nTel"}
    ]
    
    for area in areas:
        # Draw background
        draw.rectangle(area["rect"], fill=area["color"])
        
        # Draw decorative circle (White with semi-transparent)
        r_w = area["rect"][1][0] - area["rect"][0][0]
        c_x = area["rect"][0][0] + r_w // 2
        c_y = height // 2
        radius = 320
        draw.ellipse((c_x - radius, c_y - radius, c_x + radius, c_y + radius), fill="#FFFFFF80") 
        
        # Draw Text
        text = area["text"]
        
        # Calculate text position (Centered)
        # multiline_textbbox is better for multi-line
        left, top, right, bottom = draw.multiline_textbbox((0, 0), text, font=font, align="center")
        text_w = right - left
        text_h = bottom - top
        
        draw.multiline_text((c_x - text_w // 2, c_y - text_h // 2), text, font=font, fill=text_color, align="center")
        
        # Draw borders
        draw.line([area["rect"][1][0], 0, area["rect"][1][0], height], fill="white", width=8)
    
    # Save
    img.save(path)
    print(f"✅ Created styled image at {path}")

def setup_rich_menu():
    image_path = "rich_menu.png"
    create_rich_menu_image(image_path) # 画像を再生成

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_blob_api = MessagingApiBlob(api_client)
        
        # 1. Define Rich Menu
        rich_menu_to_create = RichMenuRequest(
            size=RichMenuSize(width=2500, height=843),
            selected=True,
            name="Salon Menu",
            chat_bar_text="メニュー",
            areas=[
                # Left: Reserve
                RichMenuArea(
                    bounds=RichMenuBounds(x=0, y=0, width=833, height=843),
                    action=MessageAction(label="予約する", text="予約")
                ),
                # Center: Cancel (Changed)
                RichMenuArea(
                    bounds=RichMenuBounds(x=833, y=0, width=833, height=843),
                    action=MessageAction(label="予約キャンセル", text="キャンセル")
                ),
                # Right: Phone
                RichMenuArea(
                    bounds=RichMenuBounds(x=1666, y=0, width=834, height=843),
                    action=URIAction(label="電話", uri="tel:0312345678")
                )
            ]
        )
        
        # 2. Create Rich Menu
        rich_menu_id = line_bot_api.create_rich_menu(rich_menu_request=rich_menu_to_create).rich_menu_id
        print(f"✅ Created Rich Menu ID: {rich_menu_id}")
        
        # 3. Upload Image
        with open(image_path, 'rb') as f:
            image_data = f.read()
            line_bot_blob_api.set_rich_menu_image(
                rich_menu_id=rich_menu_id,
                body=image_data,
                _headers={'Content-Type': 'image/jpeg'}
            )
        print("✅ Uploaded Rich Menu Image")
        
        # 4. Set as Default
        line_bot_api.set_default_rich_menu(rich_menu_id=rich_menu_id)
        print("✅ Set as Default Rich Menu")

        # 5. Force Link to User (Specific User)
        # ログからユーザーIDを特定するか、これまで使っていたIDを使用
        target_user_id = "Ua6c2de2f53816a8ea4137ab956cd8812" 
        line_bot_api.link_rich_menu_id_to_user(
            user_id=target_user_id,
            rich_menu_id=rich_menu_id
        )
        print(f"✅ Forced Link to User: {target_user_id}")

if __name__ == "__main__":
    setup_rich_menu()
