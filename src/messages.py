from linebot.v3.messaging import (
    FlexMessage,
    FlexContainer
)
import json

def get_menu_flex_message():
    """
    予約メニュー選択用のFlex Messageを生成する
    """
    flex_json = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": "https://images.unsplash.com/photo-1560066984-138dadb4c035?ixlib=rb-1.2.1&auto=format&fit=crop&w=1000&q=80",
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
            "action": {
                "type": "uri",
                "uri": "http://linecorp.com/"
            }
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "MENU SELECT",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#1DB446"
                },
                {
                    "type": "text",
                    "text": "ご希望のメニューを選択してください",
                    "size": "sm",
                    "color": "#aaaaaa",
                    "wrap": True
                },
                {
                    "type": "separator",
                    "margin": "xxl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "xxl",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "message",
                                "label": "✂️ カット (60分)",
                                "text": "メニュー: カット"
                            },
                            "style": "secondary",
                            "height": "sm"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "message",
                                "label": "🎨 カラー (90分)",
                                "text": "メニュー: カラー"
                            },
                            "style": "secondary",
                            "height": "sm"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "message",
                                "label": "💆 ヘッドスパ (30分)",
                                "text": "メニュー: ヘッドスパ"
                            },
                            "style": "secondary",
                            "height": "sm"
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": "※その他のお問い合わせは直接メッセージをお送りください",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "align": "center",
                    "wrap": True
                }
            ],
            "flex": 0
        }
    }

    return FlexMessage(alt_text="メニュー選択", contents=FlexContainer.from_dict(flex_json))
