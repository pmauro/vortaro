import json
import re


def safe_str(val, prefix='', suffix=''):
    if val is not None:
        return prefix + val + suffix
    return prefix + " " + suffix


def make_link(text, url):
    return f"<a href='{url}' target='_blank'>{text}</a>"


def get_mw_word_url(word):
    return f"https://www.merriam-webster.com/dictionary/{word}"


class Sense:
    def __init__(self, sn):
        self.sense_number = sn
        self.def_text = None
        self.verbal_illustration = None
        # todo parse verbal illustration
        # todo parse sdsense

        self.sn_top = None
        self.sn_sub = None

    @staticmethod
    def parse_sense_number(raw_sn, def_sn_top=None):
        sn_split = raw_sn.split()
        if len(sn_split) == 0:
            return None, None

        sn_top, sn_sub = None, None
        if sn_split[0].isdigit():
            sn_top = sn_split[0]
            if len(sn_split) > 1:
                sn_sub = sn_split[1]
        else:
            sn_top = def_sn_top
            sn_sub = sn_split[0]
        return sn_top, sn_sub

    def set_def_text(self, dt):
        if self.def_text is not None:
            self.def_text += "&#x2192; " + dt
        else:
            self.def_text = dt

    @staticmethod
    def proc_link(raw_str, prefix, num_parts):
        if num_parts not in {1, 2, 3}:
            return

        item_str = "([a-zA-Z- :0-9]+)"
        search_str = "\{" + prefix + "\|" + item_str
        if num_parts > 1:
            search_str += "\|" + item_str + "?"
        if num_parts == 3:
            search_str += "\|" + item_str + "?"
        search_str += "\}"

        do_upper = False
        if prefix not in {"a_link", "d_link", "i_link"}:
            do_upper = True

        while True:
            match = re.search(search_str, raw_str)
            if not match:
                break

            text = match.group(1)
            link = match.group(2) if len(match.groups()) > 1 else None
            sense_number = match.group(3) if len(match.groups()) > 2 else None

            if link is None:
                link = text

            text_elements = text.split(":")
            if len(text_elements) == 1:
                if do_upper:
                    text = text.upper()
            else:
                if do_upper:
                    text = text_elements[0].upper()
                text += f" entry {text_elements[1]}"

            link_elements = link.split(":")
            if len(link_elements) == 2:
                if link_elements[1].isdigit():
                    anchor_text = f"#h{link_elements[1]}"
                else:
                    anchor_text = f"#{link_elements[1]}"
                link = link_elements[0] + anchor_text

            if sense_number is not None:
                text += f" sense {sense_number}"

            if do_upper:
                link_html = "<span style='font-size:80%;'>" + make_link(text, get_mw_word_url(link)) + "</span>"
            elif prefix == "i":
                link_html = "<em>" + make_link(text, get_mw_word_url(link)) + "</em>"
            else:
                link_html = make_link(text, get_mw_word_url(link))

            raw_str = raw_str.replace(match.group(0), link_html)

        return raw_str

    @staticmethod
    def proc_mw_text(raw_str):
        if raw_str is None or len(raw_str) == 0:
            return raw_str

        # bc - bold colon
        raw_str = raw_str.replace("{bc}", "<b>:</b>&nbsp;")
        # a_link - auto link
        raw_str = Sense.proc_link(raw_str, "a_link", 1)
        # d_link - direct link
        raw_str = Sense.proc_link(raw_str, "d_link", 2)
        # i_link - italicized link
        raw_str = Sense.proc_link(raw_str, "i_link", 2)
        # sx - synonymous cross-reference
        raw_str = Sense.proc_link(raw_str, "sx", 3)
        # dxt - directional cross-reference target
        raw_str = Sense.proc_link(raw_str, "dxt", 3)
        # dx -
        raw_str = re.sub(r"\{dx\}(.+)\{\/dx\}", r"&#x2192; \1", raw_str)
        # dx_def -
        raw_str = re.sub(r"\{dx_def\}(.+)\{\/dx_def\}", r"(\1)", raw_str)
        # it - italics
        raw_str = re.sub(r"\{it\}([a-zA-Z0-9-\. ]+)\{\/it\}", r"<em> \1 </em>", raw_str)
        # sc - small capitals
        raw_str = re.sub(r"\{sc\}([a-zA-Z0-9-\. ]+)\{\/sc\}", r"<span class='sc'> \1 </span>", raw_str)
        # phrase - phrase
        raw_str = re.sub(r"\{phrase\}([a-zA-Z0-9-\. ]+)\{\/phrase\}", r"<b><em> \1 </em></b>", raw_str)
        # inf - subscript
        raw_str = re.sub(r"\{inf\}([a-zA-Z0-9-\. ]+)\{\/inf\}", r"<span style='vertical-align:sub;'> \1 </span>", raw_str)

        return raw_str

    def __str__(self):
        ret_val = f'{self.sense_number}'
        ret_val += safe_str(self.def_text, prefix='\t')
        return ret_val

    def to_html(self):
        return Sense.proc_mw_text(str(self))

    def to_dict(self):
        ret_dict = {'sense_text': Sense.proc_mw_text(self.def_text)}
        if self.sn_top is not None:
            ret_dict['sense_number'] = self.sn_top
        if self.sn_sub is not None:
            ret_dict['sense_number_sub'] = self.sn_sub
        return ret_dict


class Definition:
    def __init__(self, hwi):
        if hwi is None:
            pass
        self.headword = Definition.parse_headword(hwi['hw'])
        self.syllables = None
        self.pronunciation = None
        self.func_label = None

        # turn into tree
        self.senses = []

        # todo add etymology

    def __str__(self):
        ret_val = f'{self.headword}'
        ret_val += safe_str(self.syllables, prefix='\n')
        ret_val += safe_str(self.pronunciation, prefix='\n')
        ret_val += safe_str(self.func_label, prefix='\n')

        for sense in self.senses:
            ret_val += "\n" + str(sense)

        return ret_val

    def to_html(self):
        return self.__str__().replace("\n", "<br>")

    def to_dict(self):
        sense_list = []
        for s in self.senses:
            sense_list.append(s.to_dict())

        return {"headword": self.headword,
                "func_label": self.func_label,
                "syllables": self.syllables,
                "pronunciation": self.pronunciation,
                "sense_list": sense_list}

    @staticmethod
    def parse_syllables(input_str):
        return input_str.replace("*", "\u2022")

    @staticmethod
    def parse_headword(input_str):
        return input_str.replace("*", "")


def parse(raw_json):
    try:
        parsed_json = json.loads(raw_json)
    except:
        return None
    # if type(parsed_json) == list:
    #     parsed_json = parsed_json[2]

    definition_list = []
    for hw_entry in parsed_json:

        if "hwi" not in hw_entry or "fl" not in hw_entry:
            continue

        if hw_entry["meta"]["section"] not in("alpha", "fwp"):
            continue

        hwi = hw_entry["hwi"]
        # wrap to catch format issues
        d = Definition(hwi)

        d.syllables = Definition.parse_syllables(hwi["hw"])
        if "prs" in hwi:
            # todo Expand to multiple pronunciations
            d.pronunciation = hwi["prs"][0]["mw"]

        d.func_label = hw_entry["fl"]

        if "def" in hw_entry:
            sense_seq = hw_entry["def"][0]['sseq']

            cur_sense_number = None
            for sense in sense_seq:
                for sense_entry in sense:
                    if sense_entry[0] == "sen":
                        cur_sense_number = sense_entry[1]["sn"]
                        continue
                    elif sense_entry[0] == "sense":
                        sense_entry_vals = sense_entry[1]
                    elif sense_entry[0] == "bs":
                        sense_entry_vals = sense_entry[1]["sense"]
                    else:
                        # todo throw warning
                        continue

                    sense_number = ""
                    if 'sn' in sense_entry_vals:
                        sense_number = sense_entry_vals['sn']

                    s = Sense(sense_number)
                    s.sn_top, s.sn_sub = Sense.parse_sense_number(sense_number, cur_sense_number)

                    for ev in sense_entry_vals['dt']:
                        if ev[0] == 'text':
                            s.set_def_text(ev[1])
                        elif ev[0] == 'uns':
                            if ev[1][0][0][0] == 'text':
                                s.set_def_text(ev[1][0][0][1])

                    d.senses.append(s)

        definition_list.append(d)

    return definition_list

def defn_list_to_dict(definition_list):
    if definition_list is None:
        return None

    output = []
    for definition in definition_list:
        output.append(definition.to_dict())
    return output



if __name__ == "__main__":
    file_name = "/Users/patrickmauro/code/dictionary/test.json"
    with open(file_name) as f:
        raw_json = str(f.readlines())[2:-2]

    defn_list = parse("ha-ha", raw_json)

    for defn in defn_list:
        print(str(defn))
        print("----")
