import logging
import os
import math
import random
from datetime import datetime


import colorsys
import requests
from typing import Dict, List
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFile import ImageFile

from maibox.wechat import WechatInterface

logger = logging.getLogger(__name__)

scoreRank = ['D', 'C', 'B', 'BB', 'BBB', 'A', 'AA', 'AAA', 'S', 'S+', 'SS', 'SS+', 'SSS', 'SSS+']
combo = ['', 'FC', 'FC+', 'AP', 'AP+']
diffs = ['Basic', 'Advanced', 'Expert', 'Master', 'Re:Master']
maimaiImgPath = r'static/images/maimai'
materialPath = r'static/material'

def get_cover_len5_id(mid) -> str:
    mid = int(mid)
    if 10000 < mid <= 11000:
        mid -= 10000
    return f'{mid:05d}'

def get_cover_len6_id(mid) -> str:
    return f'{mid%10000:06d}'

def generateBaseImg_festival():
    BaseImg = Image.open(rf"{maimaiImgPath}/Style-Buddies/bg_B50.png")
    return BaseImg


def circle_corner(img, radii=30):
    # 白色区域透明可见，黑色区域不可见
    circle = Image.new('L', (radii * 2, radii * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)

    img = img.convert("RGBA")
    w, h = img.size

    # 画角
    alpha = Image.new('L', img.size, 255)
    alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))  # 左上角
    alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))  # 右上角
    alpha.paste(circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii))  # 右下角
    alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))  # 左下角

    img.putalpha(alpha)

    return img

def drawBaseImg(sd,dx,B35Rating,B15Rating,rankRating,userData,userName,plate,icon, filename):
    BaseImg = generateBaseImg_festival()

    totalRating = int(B35Rating)+int(B15Rating)
    title = f"B35：{B35Rating} + B15：{B15Rating}"

    UserImg = drawUserImg(userData,title,totalRating,rankRating,userName,icon,plate)
    BaseImg.paste(UserImg, (0, 30), UserImg)

    dxLogo = Image.open(rf"{maimaiImgPath}/logo2024.png")
    dxLogo = dxLogo.resize((308, 178))
    BaseImg.paste(dxLogo, (10, 5), dxLogo)

    rankScores = [0,0]
    baseLine = 280
    stIconImg = Image.open(rf"{maimaiImgPath}/UI_GRS_Base_Achievment_00.png")
    BaseImg.paste(stIconImg, (120, baseLine-40), stIconImg)

    count = 0
    for line in sd:
        count += 1
        singleImg = drawSignleImg(line,count)
        x = 150 + 400*(int((count-1)%5))+40*int((count-1)%5)
        y = baseLine + int((count-1)/5)*100 + int((count-1)/5)*10
        BaseImg.paste(singleImg,(int(x),int(y)),singleImg)
        rankScores[0] += int(line['ra'])
    rankScoresDraw = ImageDraw.Draw(BaseImg)
    rankScoresDraw.text((330, baseLine-35), f"B35:{B35Rating}", font=ImageFont.truetype(rf'{materialPath}/STHUPO.TTF', 20),fill=(0, 0, 0))

    baseLine = baseLine + 800 + 60
    dxIconImg = Image.open(rf"{maimaiImgPath}/UI_GRS_Base_Achievment_01.png")
    BaseImg.paste(dxIconImg, (120, baseLine - 40), dxIconImg)
    count = 0
    for line in dx:
        count += 1
        singleImg = drawSignleImg(line, count)
        x = 150 + 400 * (int((count - 1) % 5)) + 40 * int((count - 1) % 5)
        y = baseLine + int((count - 1) / 5) * 100 + int((count - 1) / 5) * 10
        BaseImg.paste(singleImg, (int(x), int(y)), singleImg)
        rankScores[1] += int(line['ra'])
    rankScoresDraw = ImageDraw.Draw(BaseImg)
    rankScoresDraw.text((330, baseLine - 35), f"B15:{B15Rating}",font=ImageFont.truetype(rf'{materialPath}/STHUPO.TTF', 20), fill=(0, 0, 0))

    designDraw = ImageDraw.Draw(BaseImg)
    designDraw.text((40, 1505), f"{filename} - Generated by maibox-wx at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} (thanks fuBot-HCskia)",font=ImageFont.truetype(rf'{materialPath}/GenSenMaruGothicTW-Bold.ttf', 20), fill=(255, 255, 255))

    return BaseImg

def drawUserImg(data,title,totalRating,rankRating,userName,icon,plate,title_rare="Normal",classRank=-1):
    numToNum = {    '0': "UI_NUM_Drating_0.png",
                    '1': "UI_NUM_Drating_1.png",
                    '2': "UI_NUM_Drating_2.png",
                    '3': "UI_NUM_Drating_3.png",
                    '4': "UI_NUM_Drating_4.png",
                    '5': "UI_NUM_Drating_5.png",
                    '6': "UI_NUM_Drating_6.png",
                    '7': "UI_NUM_Drating_7.png",
                    '8': "UI_NUM_Drating_8.png",
                    '9': "UI_NUM_Drating_9.png"}

    UserImg = Image.new('RGBA', (2500, 200))

    plateImg = Image.open(plate)
    plateImg = plateImg.resize((720,116))
    UserImg.paste(plateImg, (830, 8), plateImg)

    iconImg = Image.open(icon)
    iconImg = iconImg.resize((100,100))
    UserImg.paste(iconImg,(835,15),iconImg)


    if 0 <= totalRating <= 999:
        ratingPlate = "UI_CMN_DXRating_01.png"
    elif 1000 <= totalRating <= 1999:
        ratingPlate = "UI_CMN_DXRating_02.png"
    elif 2000 <= totalRating <= 3999:
        ratingPlate = "UI_CMN_DXRating_03.png"
    elif 4000 <= totalRating <= 6999:
        ratingPlate = "UI_CMN_DXRating_04.png"
    elif 7000 <= totalRating <= 9999:
        ratingPlate = "UI_CMN_DXRating_05.png"
    elif 10000 <= totalRating <= 11999:
        ratingPlate = "UI_CMN_DXRating_06.png"
    elif 12000 <= totalRating <= 12999:
        ratingPlate = "UI_CMN_DXRating_07.png"
    elif 13000 <= totalRating <= 13999:
        ratingPlate = "UI_CMN_DXRating_08.png"
    elif 14000 <= totalRating <= 14499:
        ratingPlate = "UI_CMN_DXRating_09.png"
    elif 14500 <= totalRating <= 14999:
        ratingPlate = "UI_CMN_DXRating_10.png"
    else:
        ratingPlate = "UI_CMN_DXRating_11.png"

    ratingPlateImg = Image.open(rf"{maimaiImgPath}/Rating/{ratingPlate}").resize((174,36))
    UserImg.paste(ratingPlateImg, (940, 16), ratingPlateImg)

    # 定义偏移量和初始x坐标
    offset = 15
    start_x = 1081
    x_positions = [start_x - i * offset for i in range(len(str(totalRating)))][:5]

    # 根据totalRating的位数处理图片
    for i, x_pos in enumerate(x_positions):
        # 计算当前位上的数字
        digit = int(totalRating / (10 ** i) % 10)
        # 打开并调整图片大小
        numImg = Image.open(rf"{maimaiImgPath}/num/{numToNum[f'{digit}']}").resize((21, 23))
        # 粘贴图片
        UserImg.paste(numImg, (x_pos, 23), numImg)

    if 25 >= int(classRank) >= 0:
        classRankImg = Image.open(rf"{maimaiImgPath}/classRank/UI_CMN_Class_S_{int(classRank):02d}.png").resize((84, 50))
        UserImg.paste(classRankImg, (1114, 7), classRankImg)


    UserIdImg = circle_corner(Image.new('RGBA', (260, 40), color=(255, 255, 255)),5)
    UserIdDraw = ImageDraw.Draw(UserIdImg)
    UserIdDraw.text((7, 12), f"{userName}", font=ImageFont.truetype(rf'{materialPath}/GenSenMaruGothicTW-Medium.ttf', 20),fill=(0, 0, 0))
    UserImg.paste(UserIdImg, (940, 50), UserIdImg)

    if 23 >= int(rankRating) >= 0:
        rankImg = Image.open(rf"{maimaiImgPath}/Ranks/{int(rankRating)}.png").resize((74, 34))
        UserImg.paste(rankImg, (1120, 55), rankImg)

    totalRatingImg = Image.open(rf"{maimaiImgPath}/shougou/UI_CMN_Shougou_{title_rare.title()}.png")#421*92  227*50
    totalRatingDraw = ImageDraw.Draw(totalRatingImg)
    totalRatingDraw.text((10, 7), title, font=ImageFont.truetype(rf'{materialPath}/GenSenMaruGothicTW-Bold.ttf', 11),fill=(0, 0, 0))
    UserImg.paste(totalRatingImg, (940, 92), totalRatingImg)

    return UserImg



def drawSignleImg(data,count):
    fcNameToFile = {'fc': "UI_MSS_MBase_Icon_FC.png",
                    'fcp': "UI_MSS_MBase_Icon_FCp.png",
                    'ap': "UI_MSS_MBase_Icon_AP.png",
                    'app': "UI_MSS_MBase_Icon_APp.png"}
    fsNameToFile = {'fs': "UI_MSS_MBase_Icon_FS.png",
                    'fsp': "UI_MSS_MBase_Icon_FSD.png",
                    'fsd': "UI_MSS_MBase_Icon_FSDp.png",
                    'fsdp': "UI_MSS_MBase_Icon_FSp.png",
                    "sync": "UI_MSS_MBase_Icon_SP.png"}
    baseNameToFile = {'d': "UI_GAM_Rank_D.png",
                      'c': "UI_GAM_Rank_C.png",
                      'b': "UI_GAM_Rank_B.png",
                      'bb': "UI_GAM_Rank_BB.png",
                      'bbb': "UI_GAM_Rank_BBB.png",
                      'a': "UI_GAM_Rank_A.png",
                      'aa': "UI_GAM_Rank_AA.png",
                      'aaa': "UI_GAM_Rank_AAA.png",
                      's': "UI_GAM_Rank_S.png",
                      'sp': "UI_GAM_Rank_Sp.png",
                      'ss': "UI_GAM_Rank_SS.png",
                      'ssp': "UI_GAM_Rank_SSp.png",
                      'sss': "UI_GAM_Rank_SSS.png",
                      'sssp': "UI_GAM_Rank_SSSp.png"}
    rankIcon = {'Basic': "diff_basic.png",
                'Advanced': "diff_advanced.png",
                'Expert': "diff_expert.png",
                'Master': "diff_master.png",
                'Re:MASTER': "diff_remaster.png"}
    levelToColor = {'Basic': (153, 255, 102),
                    'Advanced': (255, 242, 102),
                    'Expert': (255, 55, 55),
                    'Master': (191, 55, 255),
                    'Re:MASTER': (238, 202, 255)}
    coverFront = ImageFont.truetype(rf'{materialPath}/GenSenMaruGothicTW-Bold.ttf', 10)
    singleBaseImg = Image.new('RGB', (400, 100), color=(7, 86, 156)).convert("RGBA")

    underImg = Image.new('RGB', (400, 20), color=(255, 255, 255))
    underTextDraw = ImageDraw.Draw(underImg)
    underTextDraw.text((109, 0), f"#{count}", font=ImageFont.truetype(rf'{materialPath}/GenSenMaruGothicTW-Bold.ttf', 16),fill=(0, 0, 0))
    raImg = Image.open(rf"{maimaiImgPath}/rating.png").resize((48,9))
    underImg.paste(raImg,(150,0),raImg)
    underTextDraw.text((165, 7), f"{data['ds']}",font=ImageFont.truetype(rf'{materialPath}/GenSenMaruGothicTW-Bold.ttf', 10), fill=(0, 0, 0))
    underTextDraw.text((200, 0), f">{computeRa(data['ds'],data['achievements'])}", font=ImageFont.truetype(rf'{materialPath}/GenSenMaruGothicTW-Bold.ttf', 16),fill=(0, 0, 0))
    dxScoreImg = Image.open(rf"{maimaiImgPath}/deluxscore.png").resize((72,17))
    underImg.paste(dxScoreImg,(270,2),dxScoreImg)
    underTextDraw.text((337, 0), f"{data['dxScore']}",font=ImageFont.truetype(rf'{materialPath}/GenSenMaruGothicTW-Bold.ttf', 16), fill=(29, 164, 0))

    singleBaseImg.paste(underImg, (0, 80))


    try:
        cover = Image.open(rf"{maimaiImgPath}/covers/UI_Jacket_{get_cover_len6_id(data['song_id'])}.png")
        cover = cover.resize((90, 90))
    except FileNotFoundError:
        try:
            coverDownload = requests.get(f"https://www.diving-fish.com/covers/{get_cover_len5_id(data['song_id'])}.png")
            with open(rf"{maimaiImgPath}/covers/UI_Jacket_{get_cover_len6_id(data['song_id'])}.png", 'wb+')as f:
                f.write(coverDownload.content)
                f.close()
            logger.info(f"[maimaiDX]歌曲{get_cover_len6_id(data['song_id'])}封面下载成功！")
            cover = Image.open(f"{maimaiImgPath}/covers/UI_Jacket_{get_cover_len6_id(data['song_id'])}.png")
            cover = cover.resize((90, 90))
        except:
            try:
                id = str(data['song_id'])
                if "10" in id:
                    id = id.replace("10", "")
                else:
                    id = "10" + id
                logger.info(id)
                cover = Image.open(rf"{maimaiImgPath}/covers/UI_Jacket_{get_cover_len6_id(id)}.png")
                cover = cover.resize((90, 90))
            except:
                try:
                    os.remove(f"{maimaiImgPath}/covers/UI_Jacket_{get_cover_len6_id(data['song_id'])}.png")
                except:
                    pass
                logger.info(f"[maimaiDX]歌曲{data['song_id']}暂无封面")
                cover = Image.open(rf"{maimaiImgPath}/covers/UI_Jacket_000000.png")  # 错误回退封面
                cover = cover.resize((90, 90))

    coverBg = Image.new('RGB', (100, 100), color=levelToColor[f"{data['level_label']}"])
    coverBg.paste(cover, (5, 5))
    cover = coverBg
    rankImg = Image.open(rf"""{maimaiImgPath}/Diff/{rankIcon[f"{data['level_label']}"]}""")
    dxImg = Image.open(rf"{maimaiImgPath}/UI_CMN_Name_DX.png")
    dxImg = dxImg.resize((30, 21))
    singleBaseImg.paste(cover,(0, 0))
    singleBaseImg.paste(rankImg, (100, 1), rankImg)
    if data['type'] == "DX":
        singleBaseImg.paste(dxImg, (60, 69), dxImg)
    processImg = Image.open(rf"""{maimaiImgPath}/Rank/{baseNameToFile[f"{data['rate']}"]}""")
    singleBaseImg.paste(processImg, (290, 30), processImg)
    textDraw = ImageDraw.Draw(singleBaseImg)
    textDraw.text((245, 15), f"id:{data['song_id']}",font=ImageFont.truetype(rf'{materialPath}/STHUPO.TTF', 12), fill=(255, 255, 255))
    title = data['title']
    if _coloumWidth(title) > 15:
        title = _changeColumnWidth(title, 14) + '...'
    textDraw.text((107,27), f"{title}", font=ImageFont.truetype(rf'{materialPath}/GenSenMaruGothicTW-Bold.ttf', 20), fill=(255, 255, 255))
    textDraw.text((103, 50), f"{float(data['achievements']):.04f}%", font=ImageFont.truetype(rf'{materialPath}/STHUPO.TTF', 30), fill=(255, 255, 255))
    blanIconImg = Image.open(rf"{maimaiImgPath}/Fc/UI_MSS_MBase_Icon_Blank.png")
    blanIconImg = blanIconImg.resize((28,28))
    singleBaseImg.paste(blanIconImg, (337, 3), blanIconImg)
    singleBaseImg.paste(blanIconImg, (306, 3), blanIconImg)

    if data['fc'] != "":
        fcIconImg = Image.open(rf"""{maimaiImgPath}/Fc/{fcNameToFile[f"{data['fc']}"]}""")
        fcIconImg = fcIconImg.resize((28,28))
        singleBaseImg.paste(fcIconImg, (337, 3), fcIconImg)
    if data['fs'] != "":
        fsIconImg = Image.open(rf"""{maimaiImgPath}/Fc/{fsNameToFile[f"{data['fs']}"]}""")
        fsIconImg = fsIconImg.resize((28, 28))
        singleBaseImg.paste(fsIconImg, (306, 3), fsIconImg)

    return singleBaseImg



def _getCharWidth(o) -> int:
    widths = [
        (126, 1), (159, 0), (687, 1), (710, 0), (711, 1), (727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0),
        (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1), (8426, 0), (9000, 1), (9002, 2), (11021, 1),
        (12350, 2), (12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1), (55203, 2), (63743, 1),
        (64106, 2), (65039, 1), (65059, 0), (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
        (120831, 1), (262141, 2), (1114109, 1),
    ]
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1



def _coloumWidth(s:str):
    res = 0
    for ch in s:
        res += _getCharWidth(ord(ch))
    return res



def _changeColumnWidth(str, len):
    res = 0
    sList = []
    for ch in str:
        res += _getCharWidth(ord(ch))
        if res <= len:
            sList.append(ch)
    return ''.join(sList)



def computeRa(ds: float, achievement:float) -> int:
    baseRa = 22.4
    if achievement < 50:
        baseRa = 7.0
    elif achievement < 60:
        baseRa = 8.0
    elif achievement < 70:
        baseRa = 9.6
    elif achievement < 75:
        baseRa = 11.2
    elif achievement < 80:
        baseRa = 12.0
    elif achievement < 90:
        baseRa = 13.6
    elif achievement < 94:
        baseRa = 15.2
    elif achievement < 97:
        baseRa = 16.8
    elif achievement < 98:
        baseRa = 20.0
    elif achievement < 99:
        baseRa = 20.3
    elif achievement < 99.5:
        baseRa = 20.8
    elif achievement < 100:
        baseRa = 21.1
    elif achievement < 100.5:
        baseRa = 21.6
    return math.floor(ds * (min(100.5, achievement) / 100) * baseRa)

def getRandomPlate():
    plateList = []
    for root, dirs, files in os.walk(rf'{maimaiImgPath}/plate/normal'):
        for file in files:
            file = str(os.path.join(file))
            if 'UI_Plate' not in file:
                continue
            plateList.append(file)
    return rf"{maimaiImgPath}/plate/normal/{plateList[random.randint(0, len(plateList) - 1)]}"

def getRandomIcon():
    iconList = []
    for root, dirs, files in os.walk(rf'{maimaiImgPath}/icon'):
        for file in files:
            file = str(os.path.join(file))
            if 'UI_Icon' not in file:
                continue
            iconList.append(file)
    return rf"{maimaiImgPath}/icon/{iconList[random.randint(0, len(iconList) - 1)]}"


def generate(payload: Dict, nickname: str="", icon_id: int=0, filename="") -> ImageFile | None:
    resp = requests.request("POST", "https://www.diving-fish.com/api/maimaidxprober/query/player", json=payload)
    if resp.status_code == 400:
        return None
    if resp.status_code == 403:
        return None
    obj = resp.json()

    if obj['user_general_data'] is not None :
        if nickname:
            obj['nickname'] = nickname


    logger.info(obj)
    dx: List[Dict] = obj["charts"]["dx"]
    sd: List[Dict] = obj["charts"]["sd"]
    B35Rating = 0
    B15Rating = 0
    for t in sd:
        B35Rating += int(computeRa(t['ds'], t['achievements']))
    for t in dx:
        B15Rating += int(computeRa(t['ds'], t['achievements']))
    plate = None
    icon = None
    if obj['user_general_data'] == None:
        if (obj['plate'] == None) or (obj['plate'] == ''):
            plate = getRandomPlate()
        icon = getRandomIcon()

    achievePath = []
    for root, dirs, files in os.walk(rf"{maimaiImgPath}/plate/achievements"):
        for t in files:
            achievePath.append(str(t).replace('.png',''))

    if plate == None:
        if obj['plate'] in achievePath:
            plate = rf"{maimaiImgPath}/plate/achievements/{obj['plate']}.png"
        else:
            plate = rf"{maimaiImgPath}/plate/normal/UI_Plate_{str(obj['user_general_data']['plateId']).zfill(6)}.png"
        try:
            Image.open(plate)
        except:
            plate = getRandomPlate()

    if icon_id:
        icon = rf"{maimaiImgPath}/icon/UI_Icon_{str(icon_id).zfill(6)}.png"

    if nickname:
        obj['nickname'] = nickname

    if icon == None:
        try:
            Image.open(rf"{maimaiImgPath}/icon/UI_Icon_{str(obj['user_general_data']['iconId']).zfill(6)}.png")
            icon = rf"{maimaiImgPath}/icon/UI_Icon_{str(obj['user_general_data']['iconId']).zfill(6)}.png"
        except:
            icon = getRandomIcon()

    return drawBaseImg(sd, dx, B35Rating, B15Rating, int(obj['additional_rating']), obj["user_general_data"], obj["nickname"], plate, icon, filename)


def get_dominant_color(image):
    # 颜色模式转换，以便输出rgb颜色值
    image = image.convert('RGBA')
    # 生成缩略图，减少计算量，减小cpu压力
    image.thumbnail((200, 200))
    max_score = 0
    dominant_color = (0,0,0)
    for count, (r, g, b, a) in image.getcolors(image.size[0] * image.size[1]):
        # 跳过纯黑色
        if a == 0:
            continue
        saturation = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)[1]
        y = min(abs(r * 2104 + g * 4130 + b * 802 + 4096 + 131072) >> 13, 235)
        y = (y - 16.0) / (235 - 16)
        # 忽略高亮色
        if y > 0.9:
            continue
        score = (saturation + 0.1) * count
        if score > max_score:
            max_score = score
            dominant_color = (r, g, b)
    return dominant_color


def draw_text_with_stroke(draw: ImageDraw, pos, text, font, fill_color, stroke_width=2, stroke_color='white'):
    # 绘制描边
    for x_offset in range(-stroke_width+1, stroke_width):
        for y_offset in range(-stroke_width+1, stroke_width):
            if x_offset == 0 and y_offset == 0:
                continue
            draw.text((pos[0] + x_offset, pos[1] + y_offset), text, font=font, fill=stroke_color)

    # 在正确位置绘制文本
    draw.text(pos, text, font=font, fill=fill_color)

def draw_text_with_stroke_and_spacing(draw: ImageDraw.ImageDraw, pos, text, font, fill_color, stroke_width=2, stroke_color='white', spacing=5):
    # 绘制描边
    for x_offset in range(-stroke_width+1, stroke_width):
        for y_offset in range(-stroke_width+1, stroke_width):
            if x_offset == 0 and y_offset == 0:
                continue
            xx, yy = (pos[0] + x_offset, pos[1] + y_offset)
            for char in text:
                _, _, char_width, _ = draw.textbbox((0, 0), char, font=font)  # 'W' 是一个较宽的字符，用于估算
                draw.text((xx, yy), char, font=font, fill=stroke_color)
                xx += char_width + spacing  # 增加间距

    # 逐字符绘制并调整位置
    x, y = pos
    for char in text:
        _, _, char_width, _ = draw.textbbox((0, 0), char, font=font)  # 'W' 是一个较宽的字符，用于估算
        draw.text((x, y), char, font=font, fill=fill_color)
        x += char_width + spacing  # 增加间距

def draw_text_with_spacing(draw: ImageDraw.ImageDraw, pos, text, font, fill_color, spacing=5):
    # 逐字符绘制并调整位置
    x, y = pos
    for char in text:
        _, _, char_width, _ = draw.textbbox((0, 0), char, font=font)  # 'W' 是一个较宽的字符，用于估算
        draw.text((x, y), char, font=font, fill=fill_color)
        x += char_width + spacing  # 增加间距


def call_b50(fish_username, filename, nickname=None, icon_id=None, wechat_utils: WechatInterface = None, non_hashed_wxid: str=""):
    with open(f"img/{filename}.flag", "wb") as f:
        f.write(b"")
    B50Img: Image = generate({'username': fish_username, 'b50': True}, nickname, icon_id, filename).convert("RGB")
    B50Img.save(f"./img/{filename}", format="png", quality=90)

    if wechat_utils and wechat_utils.interface_test():
        wechat_utils.send_image(f"./img/{filename}", non_hashed_wxid)
        os.remove(f"./img/{filename}")

    os.remove(f"./img/{filename}.flag")

def call_user_img(filename, user_data, wechat_utils: WechatInterface = None, non_hashed_wxid: str=""):
    with open(f"img/{filename}.flag", "wb") as f:
        f.write(b"")

    try:
        frame_path = rf"{maimaiImgPath}/frame/UI_Frame_{str(user_data["frame"]).zfill(6)}.png"
        frame_img = Image.open(frame_path).resize((1080, 452))
    except:
        frame_path = rf"{maimaiImgPath}/frame/UI_Frame_000000.png"
        frame_img = Image.open(frame_path).resize((1080, 452))

    theme_color = get_dominant_color(frame_img)
    img = Image.new("RGBA", (1080, 477), theme_color)
    text_color = tuple(abs(c-100)%255 for c in theme_color)

    img.paste(frame_img, (0, 0))

    plate = rf"{maimaiImgPath}/plate/normal/UI_Plate_{str(user_data['plate']).zfill(6)}.png"
    icon = rf"{maimaiImgPath}/icon/UI_Icon_{str(user_data['icon']).zfill(6)}.png"

    UserImg: Image = drawUserImg(user_data, user_data["title"], user_data["rating"], user_data['courseRank'], user_data['nickname'], icon, plate,user_data["titleRare"],user_data["classRank"]).crop((830,8,1550,124))
    img.paste(UserImg, (25, 25), UserImg)

    network_status_img = Image.open(rf"{maimaiImgPath}/network/on.png")
    img.paste(network_status_img, (1014, 25), network_status_img)

    designDraw = ImageDraw.Draw(img)
    draw_text_with_stroke_and_spacing(
        designDraw,
        (922, 70),
        f"{user_data["version"]}",
        font=ImageFont.truetype(rf'{materialPath}/GenSenMaruGothicTW-Light.ttf', 18),
        fill_color="white",
        stroke_width=2,
        stroke_color='black',
        spacing=2
    )


    draw_text_with_stroke_and_spacing(
        designDraw,
        (815, 28),
        f"可用点数   24",
        font=ImageFont.truetype(rf'{materialPath}/GenSenMaruGothicTW-Light.ttf', 22),
        fill_color="white",
        stroke_width=2,
        stroke_color='black',
        spacing=2
    )

    track_img = Image.open(rf"{maimaiImgPath}/track.png")
    img.paste(track_img, (820, 90), track_img)

    designDraw.text((20, 457),
                    f"{filename} - Generated by maibox-wx at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - 图片仅供参考",
                    font=ImageFont.truetype(rf'{materialPath}/GenSenMaruGothicTW-Bold.ttf', 12), fill=text_color)

    img.save(f"./img/{filename}", format="png", quality=90)

    if wechat_utils and wechat_utils.interface_test():
        wechat_utils.send_image(f"./img/{filename}", non_hashed_wxid)
        os.remove(f"./img/{filename}")

    os.remove(f"./img/{filename}.flag")

