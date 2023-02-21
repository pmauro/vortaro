import json
import re


def safe_str(val, prefix='', suffix=''):
    if val is not None:
        return prefix + val + suffix
    return prefix + " " + suffix


class Sense:
    def __init__(self, sn):
        self.sense_number = sn
        self.def_text = None
        self.verbal_illustration = None
        # todo parse verbal illustration
        # todo parse sdsense

    def set_def_text(self, dt):
        if self.def_text is not None:
            pass

        self.def_text = dt

    @staticmethod
    def proc_mw_text(raw_str):
        raw_str = raw_str.replace("{bc}", "<b>:</b>&nbsp;")
        raw_str = re.sub(r"\{[ad]_link\|(\w+)(\|\S+)?\}", r"\1", raw_str)
        raw_str = re.sub(r"\{sx\|([a-z ]+)\|(\S+)?\|(\S+)?\}", r"\1", raw_str)
        return raw_str

    def __str__(self):
        ret_val = f'{self.sense_number}'
        ret_val += safe_str(self.def_text, prefix='\t')
        return ret_val

    def to_html(self):
        return Sense.proc_mw_text(str(self))

    def to_dict(self):
        return {'sense_number': self.sense_number,
                'sense_text': Sense.proc_mw_text(self.def_text)}


class Definition:
    def __init__(self, headword):
        if headword is None:
            pass
        self.headword = headword
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
                "syllables": self.syllables,
                "pronunciation": self.pronunciation,
                "sense_list": sense_list}

    @staticmethod
    def parse_syllables(input_str):
        return input_str.replace("*", "\u2022")


def parse(headword, raw_json):
        parsed_json = json.loads(raw_json)
    except:
        return None
    if type(parsed_json) == list:
        parsed_json = parsed_json[0]

    if "hwi" not in parsed_json:
        return None

    d = Definition(headword)

    # wrap to catch format issues

    if "hwi" in parsed_json:
        hwi = parsed_json["hwi"]

        d.syllables = Definition.parse_syllables(hwi["hw"])

        if "prs" in hwi:
            # todo Expand to multiple pronunciations
            d.pronunciation = hwi["prs"][0]["mw"]

    d.func_label = parsed_json["fl"]

    if "def" in parsed_json:
        sense_seq = parsed_json["def"][0]['sseq']

        for sense in sense_seq:
            for entry in sense:
                if entry[0] != "sense":
                    # todo throw warning
                    continue

                entry_vals = entry[1]
                sense_number = ""
                if 'sn' in entry_vals:
                    sense_number = entry_vals['sn']

                s = Sense(sense_number)
                for ev in entry_vals['dt']:
                    if ev[0] == 'text':
                        s.set_def_text(ev[1])

                d.senses.append(s)

    return d


if __name__ == "__main__":
    file_name = "/Users/patrickmauro/code/dictionary/flaskr/words/voluminous.json"
    with open(file_name) as f:
        raw_json = f.readlines()

    defn = parse("voluminous", str(raw_json)[3:-3])

    print(str(defn))
