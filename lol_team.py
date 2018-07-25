import requests
import base64
import json
import cv2

img_path = './lol_set.png' # 読み込む画像

GOOGLE_CLOUD_VISION_API_URL = 'https://vision.googleapis.com/v1/images:annotate?key='
API_KEY = 'APIキー' # GCPで登録したAPIのキーに書き換えてください


# Google cloud vision APIによるOCR
def request_cloud_vison_api(image_base64):
    api_url = GOOGLE_CLOUD_VISION_API_URL + API_KEY
    req_body = json.dumps({
        'requests': [{
            'image': {
                'content': image_base64.decode('utf-8') # bytes型のままではjsonに変換できないのでstring型に変換する
            },
            'features': [{
                'type': 'TEXT_DETECTION',
                'maxResults': 10,
            }]
        }]
    })
    res = requests.post(api_url, data=req_body)
    return res.json()


# 画像読み込み
def img_to_base64(filepath):
    with open(filepath, 'rb') as img:
        img_byte = img.read()
    return base64.b64encode(img_byte)


# ランクの判別
def rank_decision(rank, rank_name):
    if(u'ブロンズ' in rank):
        rank_name.append("B")
        return 800
    elif (u'シルバー' in rank):
        rank_name.append("S")
        return 1150
    elif (u'ゴールド' in rank):
        rank_name.append("G")
        return 1500
    elif (u'プラチナ' in rank):
        rank_name.append("P")
        return 1850
    elif (u'ダイヤモンド' in rank):
        rank_name.append("D")
        return 2200
    elif (u'マスター' in rank):
        rank_name.append("M")
        return 2550
    elif (u'チャレンジャー' in rank):
        rank_name.append("C")
        return 2700
    elif (u'アンランク' in rank):
        rank_name.append("U")
        return 940

# ディビジョンの判別
def rank_division(division, rank_array):
    if (u'Ⅳ' in division.upper()):
        rank_array.append("4")
        return 0
    elif (u'V' in division.upper()):
        rank_array.append("5")
        return 70
    elif (u'111' in division):
        rank_array.append("3")
        return 140
    elif (u'11' in division):
        rank_array.append("2")
        return 210
    elif (u'!' in division):
        rank_array.append("1")
        return 280
    else:
        rank_array.append("0")
        return 0


def listExcludedIndices(data, indices=[]):
  return [x for i, x in enumerate(data) if i not in indices]

# チーム分けのすべての組み合わせを求める
def kumiawase(leng):
    result = []
    data = list(range(leng))
    for i in range(leng):
        for j in range(i, leng - 1):
            for k in range(j, leng - 2):
                for l in range(k, leng - 3):
                    for m in range(l, leng - 4):
                           jdata = listExcludedIndices(data, [j])
                           kdata = listExcludedIndices(jdata, [k])
                           ldata = listExcludedIndices(kdata, [l])
                           mdata = listExcludedIndices(ldata, [m])
                           result.append([data[i], jdata[j], kdata[k], ldata[l], mdata[m]])
    return result


usr_list = []
sn_list = []
rank_list = []
im = cv2.imread(img_path)
h, w, _ = im.shape
w_cut = int(w / 200 * 14)
w_cut2 = int(w / 100 * 39)
w_range = int(w / 100 * 36)
w_rank = int(w / 200 * 60)
w_r_range = int(w / 100 * 12)
w_cut_r = int(w / 100 * 40)
h_cut = int(h / 144 * 43)
h_range = int(h / 720 * 49)
h_t1 = int(h / 720 * 49)
w_t1 = int(w / 200 * 4)
w_t2 = int(w / 200 * 83)

#サモナーネーム部分の画像切り取り
for i in range(10):
    if i < 5 :
        dst = im[h_cut+(h_range*i):h_cut+(h_range*(i+1)), w_cut:w_cut+w_range]
    else :
        dst = im[h_cut+(h_range*(i-5)):h_cut+(h_range*(i-4)), w_cut+w_cut2:w_cut+w_cut2+w_range]
    cv2.imwrite('./tmp.png',dst)
    usr_list.append(dst)
    sn_list.append( img_to_base64('./tmp.png') )

#ランク部分の画像切り取り
for i in range(10):
    if i < 5 :
        dst = im[h_cut+(h_range*i):h_cut+(h_range*(i+1)), w_rank:w_rank+w_r_range]
        cv2.imwrite('./tmp.png',dst)
        rank_list.append( img_to_base64('./tmp.png') )
        path = './cut/tmp'+ str(i) + '.png'
        cv2.imwrite(path,dst)

    else :
        dst = im[h_cut+(h_range*(i-5)):h_cut+(h_range*(i-4)), w_rank+w_cut_r:w_rank+w_cut_r+w_r_range]
        cv2.imwrite('./tmp.png',dst)
        rank_list.append( img_to_base64('./tmp.png') )
        path = './cut/tmp'+ str(i) + '.png'
        cv2.imwrite(path,dst)


#ランクをOCRによって認識
rank = []
for i in range(10):
    result = request_cloud_vison_api(rank_list[i])
    if "fullTextAnnotation" in result["responses"][0]:
        text_r = result["responses"][0]["fullTextAnnotation"]["text"].split('\n')
        rank.append(text_r[0])
    else:
        rank.append("アンランク")

mmr = []
rank_tier = []
rank_divi = []
for i in range(10):
    mmr_i = 0
    mmr_i += rank_decision(rank[i], rank_tier)
    mmr_i += rank_division(rank[i], rank_divi)
    mmr.append(mmr_i)


# MMR差が最小となるチーム分けを求める
comb10 = kumiawase(10)
min_mmr = 2000
min_team1 = []
min_team2 = []
for i in range(len(comb10)):
    team1 = 0
    team2 = 0
    team2_list = list(range(10))
    for j in range(10):
        if j in comb10[i]:
            team1 += mmr[j]
            team2_list.remove(j)
        else:
            team2 += mmr[j]

    if min_mmr > abs(team1 - team2):
        min_mmr = abs(team1 - team2)
        min_team1[0:] = comb10[i]
        min_team2[0:] = team2_list

im1 = usr_list[min_team1[0]]
im2 = usr_list[min_team1[1]]
im_h1 = cv2.vconcat([im1, im2])
im1 = usr_list[min_team2[0]]
im2 = usr_list[min_team2[1]]
im_h2 = cv2.vconcat([im1, im2])
for i in range(2,5):
    im3 = usr_list[min_team1[i]]
    im_h1 = cv2.vconcat([im_h1, im3])
    im3 = usr_list[min_team2[i]]
    im_h2 = cv2.vconcat([im_h2, im3])
im_t1 = im[h_cut-h_t1:h_cut- h_t1 + h_range, w_t1:w_t1+w_range]
im_t2 = im[h_cut-h_t1:h_cut- h_t1 + h_range, w_t2:w_t2+w_range]
im_h1 = cv2.vconcat([im_t1, im_h1])
im_h2 = cv2.vconcat([im_t2, im_h2])
im_h3 = cv2.hconcat([im_h1, im_h2])
cv2.imwrite('./team.png',im_h3)
