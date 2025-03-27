import tkinter as tk
from tkinter import messagebox, Toplevel, Text
from pathlib import Path
from llama_cpp import Llama
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

pdfmetrics.registerFont(TTFont('NotoSansTC', 'C:\\Users\\wei\\Desktop\\Noto_Sans_TC\\NotoSansTC-VariableFont_wght.ttf'))  

MODEL_PATH = "taide-7b-a.2-q4_k_m.gguf"  

taide_model = None

def load_taide_model(model_path):
    """
    加載 GGUF 格式的 taide 模型
    """
    if not Path(model_path).exists():
        raise FileNotFoundError(f"找不到模型文件: {model_path}")
    
    model = Llama(model_path=model_path)
    print(f"成功加載 taide 模型: {model_path}")
    return model

def query_model(model, prompt, max_tokens=3000, temperature=0.4):
    """
    與 GGUF 格式的 taide 模型互動
    """
    response = model(prompt=prompt, max_tokens=max_tokens, temperature=temperature)
    return response["choices"][0]["text"]

def generate_meal_plan_for_day(day, tdee, meal_calories):
    sys_prompt = "你是一個健康飲食專家，會根據使用者的 TDEE 設計膳食計劃，內容需包含具體的食物名稱與份量。"
    question = f"""
    根據每日 TDEE（每日總熱量需求）：{tdee:.2f} 大卡，生成以下一天的健康膳食計劃：
    {day}：
    早餐：{meal_calories["早餐"]:.2f} 大卡
    午餐：{meal_calories["午餐"]:.2f} 大卡
    晚餐：{meal_calories["晚餐"]:.2f} 大卡
    請列出具體食物名稱與份量。
    """
    prompt = f"<s>[INST] <<SYS>>\n{sys_prompt}\n<</SYS>>\n\n{question} [/INST]"
    
    # 模型生成
    response = query_model(taide_model, prompt=prompt, max_tokens=500, temperature=0.3)
    
    # 清理模型回傳內容
    response_lines = response.strip().split("\n")
    cleaned_response = "\n".join(line for line in response_lines if day not in line)  
    return cleaned_response

def generate_weekly_meal_plan(tdee):
    """
    遍歷每一天，生成膳食計劃
    """
    meal_calories = {
        "早餐": tdee * 0.3,
        "午餐": tdee * 0.4,
        "晚餐": tdee * 0.3
    }
    days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekly_plan = ""
    for day in days:
        daily_plan = generate_meal_plan_for_day(day, tdee, meal_calories)
        weekly_plan += f"{day}：\n{daily_plan.strip()}\n\n"  
    return weekly_plan.strip()

def calculate_bmr_tdee():
    """
    計算 BMR 和 TDEE，並顯示增肌或減脂選項
    """
    try:
        # 性別
        gender = gender_var.get()
        # 年齡、身高、體重
        age = int(age_entry.get())
        weight = float(weight_entry.get())
        height = float(height_entry.get())
        # 活動強度
        activity = activity_var.get()
        
        # 計算 BMR
        if gender == "男":
            bmr = (13.7 * weight) + (5.0 * height) - (6.8 * age) + 66
        elif gender == "女":
            bmr = (9.6 * weight) + (1.8 * height) - (4.7 * age) + 655
        else:
            raise ValueError("請選擇性別")
        
        # 根據活動強度計算 TDEE
        activity_multipliers = {
            "久坐": 1.2,
            "輕量活動": 1.375,
            "中度活動": 1.55,
            "高度活動": 1.725,
            "非常高度活動": 1.9
        }
        if activity not in activity_multipliers:
            raise ValueError("請選擇活動強度")
        
        tdee = bmr * activity_multipliers[activity]

        # 顯示結果
        bmr_result.set(f"BMR：{bmr:.2f} 大卡")
        tdee_result.set(f"TDEE：{tdee:.2f} 大卡")

        # 啟用增肌或減脂選項
        tdee_adjustment_frame.grid()
        adjust_button.config(command=lambda: adjust_tdee(tdee))
    except ValueError as e:
        messagebox.showerror("錯誤", f"輸入有誤：{e}")
    except Exception as e:
        messagebox.showerror("錯誤", f"發生未知錯誤：{e}")

def adjust_tdee(tdee):
    """
    根據增肌或減脂調整 TDEE，並啟用分析按鈕，隱藏計算按鈕
    """
    adjustment = tdee_adjustment_var.get()
    if adjustment == "增肌":
        adjusted_tdee = tdee + 300
    elif adjustment == "減脂":
        adjusted_tdee = tdee - 500
    else:
        messagebox.showerror("錯誤", "請選擇增肌或減脂")
        return

    tdee_result.set(f"調整後的 TDEE：{adjusted_tdee:.2f} 大卡")
    analyze_button.config(state="normal", command=lambda: analyze_meal_plan(adjusted_tdee))

    # 隱藏計算按鈕
    calculate_button.grid_remove()

def analyze_meal_plan(tdee):
    """
    使用調整後的 TDEE 生成膳食計劃
    """
    meal_plan = generate_weekly_meal_plan(tdee)
    show_meal_plan(meal_plan)

def show_meal_plan(meal_plan):
    """
    顯示生成的膳食計劃，並讓窗口自動調整大小
    """
    # 創建新窗口
    meal_plan_window = Toplevel(root)
    meal_plan_window.title("膳食計劃")

    # 設定行列權重，讓內容隨窗口大小變化
    meal_plan_window.grid_rowconfigure(0, weight=1)  # 第一行自動調整
    meal_plan_window.grid_columnconfigure(0, weight=1)  # 第一列自動調整

    # 創建文字框
    text_box = Text(meal_plan_window, wrap="word")
    text_box.insert("1.0", meal_plan)  # 插入膳食計劃內容
    text_box.config(state="disabled")  # 禁止編輯
    text_box.grid(row=0, column=0, sticky="nsew")  # 填滿窗口

    # 添加滾動條
    scrollbar = tk.Scrollbar(meal_plan_window, command=text_box.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")  # 滑動條佔滿窗口高度
    text_box.config(yscrollcommand=scrollbar.set)

def export_meal_plan_to_pdf(weekly_meal_plan, file_name="meal_plan.pdf"):
    """
    將膳食計劃匯出到 PDF 文件
    """
    # 初始化 PDF 文件
    pdf = canvas.Canvas(file_name, pagesize=letter)
    pdf.setFont("NotoSansTC", 12)  # 使用已註冊的字型

    page_width, page_height = letter
    x_margin = 50  # 左右邊距
    y_margin = 50  # 頂部和底部邊距
    max_width = page_width - 2 * x_margin  # 可用寬度
    y_position = page_height - y_margin  # 初始 Y 軸位置
    line_height = 20  # 行高

    days = weekly_meal_plan.strip().split("\n\n")  # 每天的膳食計劃分段

    for day_plan in days:
        lines = day_plan.split("\n")  # 每天的內容按行分割
        for line in lines:
            # 自動換行檢查
            while pdf.stringWidth(line, "NotoSansTC", 12) > max_width:
                for i in range(len(line)):
                    if pdf.stringWidth(line[:i], "NotoSansTC", 12) > max_width:
                        pdf.drawString(x_margin, y_position, line[:i-1])
                        line = line[i-1:]  # 剩餘部分
                        y_position -= line_height
                        break
            
            # 如果接近頁面底部，自動換頁
            if y_position < y_margin:
                pdf.showPage()
                pdf.setFont("NotoSansTC", 12)
                y_position = page_height - y_margin
            
            # 輸出文字
            pdf.drawString(x_margin, y_position, line.strip())
            y_position -= line_height  # 行高調整

        # 每天結束後添加空白行
        y_position -= line_height

        # 如果接近頁面底部，自動換頁
        if y_position < y_margin:
            pdf.showPage()
            pdf.setFont("NotoSansTC", 12)
            y_position = page_height - y_margin

    # 保存 PDF 文件
    pdf.save()

    # 彈出成功視窗
    root = tk.Tk()
    root.withdraw()  # 隱藏主視窗
    messagebox.showinfo("匯出成功", f"膳食計劃已成功匯出到：\n{file_name}")
    root.destroy()
    print(f"PDF 已匯出到 {file_name}")

def analyze_meal_plan(tdee):
    """
    使用調整後的 TDEE 生成膳食計劃，並啟用匯出按鈕
    """
    meal_plan = generate_weekly_meal_plan(tdee)
    show_meal_plan(meal_plan)

    # 啟用匯出按鈕
    export_button.config(state="normal", command=lambda: export_meal_plan_to_pdf(meal_plan))


root = tk.Tk()
root.title("飲食控制規劃系統")
root.geometry("600x500") 


intro_text = """
BMR（基礎代謝率）：指人體在靜止狀態下維持生命所需的最低能量需求。
TDEE（每日總熱量消耗）：是在基礎代謝率的基礎上，根據日常活動強度計算出的每日熱量需求。
增肌：在 TDEE 的基礎上增加熱量攝入，通常建議增加 300 大卡。
減脂：在 TDEE 的基礎上減少熱量攝入，通常建議減少 500 大卡。
"""
tk.Label(root, text=intro_text, justify="left", wraplength=580, fg="blue").grid(
    row=0, column=0, columnspan=3, padx=10, pady=10, sticky="w"
)

# 性別選項
gender_var = tk.StringVar(value="男")
tk.Label(root, text="你的性別：").grid(row=1, column=0, sticky="w", padx=10, pady=5)
tk.Radiobutton(root, text="男性", variable=gender_var, value="男").grid(row=1, column=1, padx=10, pady=5)
tk.Radiobutton(root, text="女性", variable=gender_var, value="女").grid(row=1, column=2, padx=10, pady=5)

# 年齡輸入
tk.Label(root, text="你的年齡：").grid(row=2, column=0, sticky="w", padx=10, pady=5)
age_entry = tk.Entry(root)
age_entry.grid(row=2, column=1, columnspan=2, padx=10, pady=5)

# 身高輸入
tk.Label(root, text="你的身高（公分）：").grid(row=3, column=0, sticky="w", padx=10, pady=5)
height_entry = tk.Entry(root)
height_entry.grid(row=3, column=1, columnspan=2, padx=10, pady=5)

# 體重輸入
tk.Label(root, text="你的體重（公斤）：").grid(row=4, column=0, sticky="w", padx=10, pady=5)
weight_entry = tk.Entry(root)
weight_entry.grid(row=4, column=1, columnspan=2, padx=10, pady=5)

# 活動強度選擇
tk.Label(root, text="每週的運動強度：").grid(row=5, column=0, sticky="w", padx=10, pady=5)
activity_var = tk.StringVar(value="久坐")
activities = [
    ("久坐（辦公室工作，無什麼運動）", "久坐"),
    ("輕量活動（每週輕鬆的運動 3-5 天）", "輕量活動"),
    ("中度活動（每週中等強度的運動 3-5 天）", "中度活動"),
    ("高度活動（每週高強度運動 6-7 天）", "高度活動"),
    ("非常高度活動 (勞力密集型工作或每天訓練甚至一天訓練兩次以上）", "非常高度活動")
]
for idx, (text, value) in enumerate(activities):
    tk.Radiobutton(root, text=text, variable=activity_var, value=value).grid(row=6+idx, column=0, columnspan=3, sticky="w", padx=10, pady=5)

# 結果顯示
bmr_result = tk.StringVar(value="")
tdee_result = tk.StringVar(value="")
tk.Label(root, textvariable=bmr_result, fg="blue").grid(row=11, column=0, columnspan=3, padx=10, pady=5)
tk.Label(root, textvariable=tdee_result, fg="green").grid(row=12, column=0, columnspan=3, padx=10, pady=5)

# 增肌/減脂選項
tdee_adjustment_frame = tk.Frame(root)  # 定義 tdee_adjustment_frame
tdee_adjustment_var = tk.StringVar(value="增肌")
tk.Label(tdee_adjustment_frame, text="選擇增肌或減脂：").grid(row=0, column=0, sticky="w", padx=10, pady=5)
tk.Radiobutton(tdee_adjustment_frame, text="增肌", variable=tdee_adjustment_var, value="增肌").grid(row=0, column=1, padx=10, pady=5)
tk.Radiobutton(tdee_adjustment_frame, text="減脂", variable=tdee_adjustment_var, value="減脂").grid(row=0, column=2, padx=10, pady=5)

# 新增一個按鈕來調整 TDEE
adjust_button = tk.Button(tdee_adjustment_frame, text="調整 TDEE", state="normal")
adjust_button.grid(row=1, column=0, columnspan=3, pady=5)
tdee_adjustment_frame.grid(row=13, column=0, columnspan=3, pady=10)
tdee_adjustment_frame.grid_remove()  # 默認隱藏

# 分析按鈕
analyze_button = tk.Button(root, text="分析", state="disabled")
analyze_button.grid(row=15, column=0, columnspan=3, pady=12)

# 計算按鈕
calculate_button = tk.Button(root, text="計算", command=calculate_bmr_tdee)
calculate_button.grid(row=14, column=0, columnspan=3, pady=12)

# 匯出到 PDF 按鈕
export_button = tk.Button(root, text="匯出到 PDF", state="disabled")
export_button.grid(row=16, column=0, columnspan=3, pady=12)

# 加載模型
try:
    taide_model = load_taide_model(MODEL_PATH)
except Exception as e:
    messagebox.showerror("模型加載失敗", f"無法加載模型：{e}")
    root.destroy()

# 運行主迴圈
root.mainloop()

