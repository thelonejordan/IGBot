import pandas as pd
import json

df = pd.read_csv("data/imagerepo.csv")
# print(df.columns)

df["fileid"] = df["link"].apply(
    lambda x: x.lstrip("https://drive.google.com/file/d/").rstrip("/view?usp=drive_link"))

df = df[["category", "description", "filename", "fileid"]]
print(df[df["category"]==1])

df_json = df.to_json(orient="index")
parsed = json.loads(df_json)
print(json.dumps(parsed, indent=4))

c3_kw = ['Fuck', 'Sex', 'Boobs', 'Ass', 'Booty', 'Breasts', 'Nude', 'Naked', 'Erotic', 'Undress', 'Pussy', 'Vagina', 'Butt']
c2_kw = ['Hot', 'Pretty', 'Sexy', 'Bikini', 'Seductive', 'Erotic', 'Sensual']
c1_kw = ['Image', 'Picture', 'Cute', 'Show', 'Baby', 'Photo', 'Pic']

def get_dict(df, category):
    req_cols = ["description", "filename", "fileid"]
    return json.loads(df[df["category"]==category][req_cols].set_index("filename").to_json(orient="index"))

final = {
    "categories": {
        "1": {
            "keywords": c1_kw,
            "images": get_dict(df, 1)
        },
        "2": {
            "keywords": c1_kw,
            "images": get_dict(df, 2)
        },
        "3": {
            "keywords": c1_kw,
            "images": get_dict(df, 3)
        }
    }
}

# print(json.dumps(final, indent=4))
path = "data/image_metadata.json"
with open(path, "w") as fp:
    json.dump(final, fp, indent=4)
    print(f"saved to: {path}")
