import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Kivy 核心組件
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput  # 引入輸入框元件
from kivy.clock import Clock
from kivy.utils import platform

# ==========================================================
# 參數與環境設定
# ==========================================================
CHINESE_FONT = "font.ttc"
URL = 'https://tw.stock.yahoo.com/future/WTX&'
SPEED_RATE = 1.25  # 語速倍率

if platform == 'win':
    import pygame
    from gtts import gTTS
    try:
        pygame.mixer.init()
    except Exception as e:
        print(f"Pygame 初始化失敗: {e}")
elif platform == 'android':
    from jnius import autoclass
    Locale = autoclass('java.util.Locale')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')

# ==========================================================
# Kivy 介面與邏輯主程式
# ==========================================================
class StockMonitorApp(App):
    def build(self):
        self.title = "期貨即時語音監控"
        self.is_monitoring = False
        self.android_tts = None
        
        # 如果是 Android，初始化原生 TTS 引擎
        if platform == 'android':
            self.android_tts = TextToSpeech(App.get_running_app().activity, None)
            self.android_tts.setLanguage(Locale.CHINESE)
            self.android_tts.setSpeechRate(SPEED_RATE)

        # 主版面
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # 1. 狀態標籤
        self.status_label = Label(
            text="狀態：未啟動監控", 
            font_size='22sp',
            font_name=CHINESE_FONT,
            size_hint=(1, 0.3)
        )
        layout.add_widget(self.status_label)
        
        # 2. 數據資訊標籤
        self.info_label = Label(
            text="最新提取數字：--", 
            font_size='18sp',
            font_name=CHINESE_FONT,
            size_hint=(1, 0.2)
        )
        layout.add_widget(self.info_label)
        
        # 3. 新增：設定時間間隔的區塊 (水平排列)
        interval_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=10)
        
        input_title = Label(
            text="查詢間隔秒數:", 
            font_size='18sp',
            font_name=CHINESE_FONT,
            size_hint=(0.5, 1)
        )
        # 建立只允許輸入數字的輸入框
        self.interval_input = TextInput(
            text="30",             # 預設 30 秒
            multiline=False, 
            font_size='18sp',
            halign='center',       # 文字置中
            input_filter='int',    # 限制只能輸入整數
            size_hint=(0.5, 1)
        )
        interval_layout.add_widget(input_title)
        interval_layout.add_widget(self.interval_input)
        layout.add_widget(interval_layout)
        
        # 4. 開始/停止按鈕
        self.btn = Button(
            text="開始監控", 
            font_size='20sp',
            font_name=CHINESE_FONT,
            size_hint=(1, 0.3),
            background_color=(0.2, 0.6, 0.8, 1)
        )
        self.btn.bind(on_press=self.toggle_monitoring)
        layout.add_widget(self.btn)
        
        return layout

    def toggle_monitoring(self, instance):
        """控制監控開關"""
        if not self.is_monitoring:
            # 讀取並驗證使用者輸入的時間間隔
            try:
                seconds = int(self.interval_input.text)
                if seconds <= 0:
                    seconds = 30  # 防呆：如果輸入 0 或負數，強制還原為 30 秒
            except ValueError:
                seconds = 30      # 防呆：如果轉換失敗，還原為 30 秒
            
            self.interval_input.text = str(seconds)
            
            # 啟動監控
            self.is_monitoring = True
            self.interval_input.disabled = True  # 監控中，禁止修改輸入框
            self.btn.text = "停止監控"
            self.btn.background_color = (0.8, 0.2, 0.2, 1)
            self.status_label.text = f"狀態：監控中 (每 {seconds} 秒)..."
            
            # 立即執行一次，並根據使用者輸入的秒數設定排程
            self.monitor_job(0)
            Clock.schedule_interval(self.monitor_job, seconds)
        else:
            # 停止監控
            self.is_monitoring = False
            self.interval_input.disabled = False  # 停止監控，解除輸入框鎖定
            self.btn.text = "開始監控"
            self.btn.background_color = (0.2, 0.6, 0.8, 1)
            self.status_label.text = "狀態：已停止監控"
            Clock.unschedule(self.monitor_job)

    def monitor_job(self, dt):
        """核心爬蟲任務"""
        now = datetime.now()
        
        # 凌晨防耗電中斷機制 (2:00 ~ 6:00 自動關閉)
        if now.hour >= 2 and now.hour < 6:
            self.status_label.text = "狀態：凌晨時間，自動關閉監控"
            self.toggle_monitoring(None)
            return

        current_time = now.strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            ua = 'Mozilla/5.0' if platform == 'win' else 'Mozilla/5.0 (Linux; Android 10; K)'
            headers = {'User-Agent': ua}
            
            response = requests.get(URL, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                span_tag = soup.select_one('span.Fz\\(32px\\).Fz\\(40px\\)--mobile') 
                
                if span_tag:
                    text_content = span_tag.text.strip()
                    no_comma_text = text_content.replace(',', '')
                    tts_text = no_comma_text.split('.')[0] if '.' in no_comma_text else no_comma_text
                    
                    self.info_label.text = f"[{current_time}] 數字: {tts_text}"
                    self.speak_text(tts_text)
                else:
                    self.info_label.text = f"[{current_time}] 錯誤: 找不到網頁標籤"
            else:
                self.info_label.text = f"[{current_time}] 請求失敗 (狀態碼: {response.status_code})"
                
        except Exception as e:
            self.info_label.text = f"[{current_time}] 網路或執行錯誤"
            print(f"Error: {e}")

    def speak_text(self, text):
        """跨平台語音播放控制"""
        if platform == 'win':
            try:
                # 1. 先解除 Pygame 對當前音訊檔的佔用，避免鎖檔
                pygame.mixer.music.unload()
                
                # 2. 為了保險起見，使用動態時間戳記命名，確保每次的檔名都不同
                timestamp = datetime.now().strftime('%H%M%S')
                temp_file = f"temp_kivy_tts_{timestamp}.mp3"
                
                # 3. 生成新語音檔案
                tts = gTTS(text=text, lang='zh-tw', slow=False)
                tts.save(temp_file)
                
                # 4. 載入並播放
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                
                # 5. 清理舊的暫存檔（嘗試刪除目錄下其他殘留的 temp_kivy_tts_*.mp3）
                # 這可以防止測試久了資料夾累積一堆垃圾檔案
                current_dir = os.getcwd()
                for file in os.listdir(current_dir):
                    if file.startswith("temp_kivy_tts_") and file.endswith(".mp3") and file != temp_file:
                        try:
                            os.remove(os.path.join(current_dir, file))
                        except Exception:
                            pass # 如果還在播，刪不掉就先不管它，下一輪再刪
                            
            except Exception as e:
                print(f"Windows 播放失敗: {e}")
                
        elif platform == 'android' and self.android_tts:
            # Android 端直接調用 API，本來就不會建立檔案，因此完全不受影響
            self.android_tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
			
if __name__ == '__main__':
    StockMonitorApp().run()
