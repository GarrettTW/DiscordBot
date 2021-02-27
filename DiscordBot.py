# bot.py
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os, sys, tempfile
import discord
from discord.ext import commands
from dotenv import load_dotenv

# 必須在同目錄下，創立檔案叫做 ".env"(前面不需要加任何檔名)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
gauth = GoogleAuth()        # 當credentials.json過期，要刪掉，然後RUN一次本Code來重新認證
gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.
drive = GoogleDrive(gauth)

# 加上一個指令觸發機器人
bot = commands.Bot(command_prefix='!',case_insensitive=True)

# 變數
GoogDrv_f_id = '???' # 雲端資料夾id
GoogDrv_player_id = '???' #雲端檔案id

def createFolder(folderName, parentID = None):
    #Create folder
    folder_metadata = {'title' : folderName, 'mimeType' : 'application/vnd.google-apps.folder'}
    if parentID:
        folder_metadata['parents'] = [{'id': parentID}]
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()

def ListFolder(parent):
    filelist={}
    file_list = drive.ListFile({'q': "'%s' in parents and trashed=false" % parent}).GetList()
    for f in file_list:
        if f['mimeType']=='application/vnd.google-apps.folder': # if folder
            filelist[f['title']] = f['id']
    return filelist

# 觸發任意事件修飾句
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# 錯誤處理
@bot.event
async def on_command_error(ctx, error):
    err_name = error.__class__.__name__
    if err_name == 'MissingRequiredArgument':
        if ctx.command.name == '加隊伍':
            Message_Tx = ":warning: 您缺少遊戲代號和隊伍名 \n 正確用法為`!加隊伍 OOO XXX` \n :one: OOO為選手遊戲代號 \n :two: XXX為想要加入的隊伍名稱 \n :three: __**加隊伍**__和__**XXX**__和__**OOO**__之間皆有空格"
        elif ctx.command.name == 'win':
            Message_Tx = ":warning: 您缺少獲勝隊伍名稱 \n 正確用法為`!win XXX` \n :one: XXX為獲勝的隊伍名稱 \n :two: __**win**__和__**XXX**__中間有一個半形空格"
        else: 
            return
        await ctx.send(Message_Tx)
    elif err_name == 'CommandNotFound':
        return
    else:
        return
        
# 處理Discord報名人數額滿
@bot.event
async def on_member_update(before, after):
    num = 0
    # 利用set建立集合
    br = set(before.roles)
    ar = set(after.roles)
    # 集合可以做邏輯運算: xor(^)會取出不同的
    # 和集合無法做其他事情，要轉為list
    diff_r = list(br^ar)
    if not diff_r:
        return
    r_0 = diff_r[0]
    r_name = r_0.name
    r_name = r_name.lower()
    
    for member in after.guild.members:
        if r_0 in member.roles:
            num=num+1
    for ch in after.guild.channels:
        ch_n = ch.name
        ch_n = ch_n.lower()
        if r_name.find(ch_n[:-1])==0:
            print(ch_n[:-1])
            if ch_n[-1] == '🚫' and num == 3:
                new_name = ch_n[:-1]+'🆗'
                await ch.edit(name=new_name)
                print(new_name) 
            if num == 4:
                new_name = ch_n[:-1]+'🚫'
                await ch.edit(name=new_name)
                print(new_name)

# 指令處理               
@bot.command(name='加隊伍')
async def cmd1(ctx, UserName, *,TeamName):
    if not ctx.message.attachments:
        print('【收到CMD】!加隊伍',UserName,TeamName,'-->但沒附截圖')
        await ctx.send(':ledger: 手機版: \n https://i.imgur.com/YefU0yA.png \n :ledger: 電腦版: \n https://i.imgur.com/EQIKjLy.png')
        await ctx.send(':warning: 指令上傳錯誤 \n 請按照上方教學來附截圖 \n '+ctx.author.mention)
        return
    print('【收到CMD】!加隊伍',UserName,TeamName)
    Message_Tx = ':thumbsup: 【指令成功】可去連結內 \n https://reurl.cc/r8aXpO \n 找到隊名資料夾: \n :point_right: `'+TeamName+'` \n 裡面會有您個人資料截圖: \n :point_right: `'+UserName+'` \n 若伺服器上傳壅塞，請五分鐘後再來看'
    
    await ctx.send(Message_Tx) 
    message_attachment = ctx.message.attachments[0]
    message_content = await message_attachment.read()
    print(message_attachment)
    
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(message_content)
        tempfile_path = tf.name
    folder = ListFolder(GoogDrv_f_id)
    folderID = folder.get(TeamName)
    if not folderID:
        createFolder(TeamName, parentID = GoogDrv_f_id)
        folder = ListFolder(GoogDrv_f_id)
        folderID = folder.get(TeamName)
    # 在雲端特定資料夾(id)內建立一個檔案
    f = drive.CreateFile({"title": UserName, "parents": [{"kind": "drive#fileLink", "id": folderID }]})  
    f.SetContentFile(tempfile_path) # 檔案的內容
    f.Upload()
    # 在雲端特定檔案(id)修改內部資訊
    p_txt = drive.CreateFile({"id":GoogDrv_player_id})
    p_txt_cnt = p_txt.GetContentString()
    p_txt.SetContentString(p_txt_cnt+"Team:"+TeamName+" Name:"+UserName+"\n")
    p_txt.Upload()
    print('【CMD成功】!加隊伍',UserName,TeamName)

@bot.command(name='win')
async def cmd2(ctx,WinTeamName):
    if not ctx.message.attachments:
        print('【收到CMD】!win',WinTeamName,'-->但沒附截圖')
        await ctx.send(':ledger: 手機版: \n https://i.imgur.com/1rqi0Yx.png \n :ledger: 電腦版: \n https://i.imgur.com/0ZJOXZ8.png')
        await ctx.send(':warning: 【指令上傳錯誤】 \n 請按照上方教學來附截圖 \n '+ctx.author.mention)
        return
    print('【收到CMD】!win',WinTeamName)   
    
    folder = ListFolder(GoogDrv_f_id)
    folderID = folder.get(WinTeamName)
    if not folderID:
        print('【失敗CMD】!win',WinTeamName,'-->隊名沒有匹配')
        Message_Tx = ':warning:【錯誤】找不到隊名資料夾為: \n :point_right: `'+WinTeamName+'` \n 請檢查隊名是否打錯(英文大小寫需相同) \n https://reurl.cc/r8aXpO '
        await ctx.send(Message_Tx)
        return  
    Message_Tx = ':thumbsup: 【指令成功】可去連結內 \n https://reurl.cc/r8aXpO \n 找到隊名資料夾: \n :point_right: `'+WinTeamName+'` \n 裡面有您剛上傳的獲勝截圖 \n 若伺服器上傳壅塞，請五分鐘後再來看'
    await ctx.send(Message_Tx) 
    message_attachment = ctx.message.attachments[0]
    message_content = await message_attachment.read()
    print(message_attachment)
    
    with tempfile.NamedTemporaryFile(delete=False) as tf: 
        tf.write(message_content)
        tempfile_path = tf.name
        
    # 在雲端建立一個檔案
    f = drive.CreateFile({"title": WinTeamName, "parents": [{"kind": "drive#fileLink", "id": folderID }]})  
    f.SetContentFile(tempfile_path) # 檔案的內容
    f.Upload()
    print('【CMD成功】!win',WinTeamName)

# main(void);
bot.run(TOKEN)
