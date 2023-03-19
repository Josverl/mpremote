from pathlib import Path
import requests

# from cachetools import cached, TTLCache
from essential_generators import DocumentGenerator, MarkovTextGenerator


# @cached(cache=TTLCache(maxsize=128, ttl=120))
def create_testfile(filename: Path, size):
    # GET text from http://metaphorpsum.com/paragraphs/3 using requests
    # write the text to a file
    txt = requests.get(f"http://metaphorpsum.com/paragraphs/{size}").text

    with open(filename, "w") as f:
        f.write(txt)


def do_stuff():
    gen = DocumentGenerator()
    print(gen.sentence())

    def nested_item():
        nested_gen = DocumentGenerator()
        nested_gen.set_template({"user": "email", "hash": "gid", "posts": int})
        return nested_gen.gen_doc()

    generator = DocumentGenerator()
    generator.set_template(
        {
            "id": "index",
            "user": nested_item,
            "url": "url",
            "age": 43,
            "one_of": ["male", "female", "both"],
        }
    )
    print(generator.gen_docs(5))

    create_testfile(Path("testfile.txt"), 10)


# do_stuff()
