'''
MIT License

Copyright (c) 2017 verixx

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import discord
from discord.ext import commands
from ext.utility import parse_equation
from ext.colours import ColorNames
from urllib.request import urlopen
from sympy import solve
from PIL import Image
import asyncio
import random
import emoji
import copy
import io
import aiohttp
import json


class Misc:
    def __init__(self, bot):
        self.bot = bot
        self.emoji_converter = commands.EmojiConverter()

    def prepare_code(self, code):
        def map_left_bracket(b, p):
            return (b, find_bracket(code, p + 1, b))

        def map_right_bracket(b, p):
            offset = find_bracket(list(reversed(code[:p])), 0, ']')
            return (b, p - offset)

        def map_bracket(b, p):
            if b == '[':
                return map_left_bracket(b, p)
            else:
                return map_right_bracket(b, p)

        return [map_bracket(c, i) if c in ('[', ']') else c
                for c, i in zip(code, range(len(code)))]

    def read(self, string):
        valid = ['>', '<', '+', '-', '.', ',', '[', ']']
        return prepare_code([c for c in string if c in valid])

    def eval_step(self, code, data, code_pos, data_pos):
        c = code[code_pos]
        d = data[data_pos]
        step = 1
        output = None

        if c == '>':
            data_pos = data_pos + 1
            if data_pos > len(data):
                data_pos = 0
        elif c == '<':
            if data_pos != 0:
                data_pos -= 1
        elif c == '+':
            if d == 255:
                data[data_pos] = 0
            else:
                data[data_pos] += 1
        elif c == '-':
            if d == 0:
                data[data_pos] = 255
            else:
                data[data_pos] -= 1
        elif c == '.':
            output = (chr(d))
        elif c == ',':
            data[data_pos] = ord(stdin.read(1))
        else:
            bracket, jmp = c
            if bracket == '[' and d == 0:
                step = 0
                code_pos = jmp
            elif bracket == ']' and d != 0:
                step = 0
                code_pos = jmp

        return (data, code_pos, data_pos, step, output)

    def bfeval(code, data=[0 for i in range(9999)], c_pos=0, d_pos=0):
        outputty = None
        while c_pos < len(code):
            out = None
            (data, c_pos, d_pos, step, output) = eval_step(code, data, c_pos, d_pos)
            if outputty == None and output == None:
                c_pos += step
            elif outputty == None and out == None and output != None:
                outputty = ''
                out = ''
                out = out + output
                outputty = outputty + out
                c_pos += step
            elif out == None and output != None:
                out = ''
                out = out + output
                outputty = outputty + out
                c_pos += step
            else:
                c_pos += step
        return outputty

    @commands.command()
    async def bf(self, ctx, slurp:str):
        '''Evaluate 'brainfuck' code (a retarded language).'''
        thruput = ctx.message.content
        preinput = thruput[5:]
        preinput2 = "\"\"\"\n" + preinput
        input = preinput2 + "\n\"\"\""
        code = read(input)
        output = bfeval(code)
        await ctx.send("Input:\n`{}`\nOutput:\n`{}`".format(preinput, output))

    @commands.command()
    async def animate(self, ctx, *, file):
        '''Animate a text file on discord!'''
        try:
            with open(f'data/anims/{file}') as a:
                anim = a.read().splitlines()
        except:
            return await ctx.send('File not found.')
        interval = anim[0]
        base = await ctx.send(anim[1])
        for line in anim[2:]:
            await base.edit(content=line)
            await asyncio.sleep(float(interval))

    @commands.command()
    async def virus(self, ctx, virus=None, *, user: discord.Member = None):
        '''
        Destroy someone's device with this virus command!
        '''
        virus = virus or 'discord'
        user = user or ctx.author
        with open('data/virus.txt') as f:
            animation = f.read().splitlines()
        base = await ctx.send(animation[0])
        for line in animation[1:]:
            await base.edit(content=line.format(virus=virus, user=user))
            await asyncio.sleep(random.randint(1, 4))

    @commands.command()
    async def react(self, ctx, index: int, *, reactions):
        '''React to a specified message with reactions'''
        history = await ctx.channel.history(limit=10).flatten()
        message = history[index]
        async for emoji in self.validate_emojis(ctx, reactions):
            await message.add_reaction(emoji)

    async def validate_emojis(self, ctx, reactions):
        '''
        Checks if an emoji is valid otherwise,
        tries to convert it into a custom emoji
        '''
        for emote in reactions.split():
            if emote in emoji.UNICODE_EMOJI:
                yield emote
            else:
                try:
                    yield await self.emoji_converter.convert(ctx, emote)
                except commands.BadArgument:
                    pass

    @commands.command(aliases=['color', 'colour', 'sc'])
    async def show_color(self, ctx, *, color: discord.Colour):
        '''Enter a color and you will see it!'''
        file = io.BytesIO()
        Image.new('RGB', (200, 90), color.to_rgb()).save(file, format='PNG')
        file.seek(0)
        em = discord.Embed(color=color, title=f'Showing Color: {str(color)}')
        em.set_image(url='attachment://color.png')
        await ctx.send(file=discord.File(file, 'color.png'), embed=em)

    @commands.command(aliases=['dc', 'dominant_color'])
    async def dcolor(self, ctx, *, url):
        '''Fun command that shows the dominant color of an image'''
        await ctx.message.delete()
        color = await ctx.get_dominant_color(url)
        string_col = ColorNames.color_name(str(color))
        info = f'`{str(color)}`\n`{color.to_rgb()}`\n`{str(string_col)}`'
        em = discord.Embed(color=color, title='Dominant Color', description=info)
        em.set_thumbnail(url=url)
        file = io.BytesIO()
        Image.new('RGB', (200, 90), color.to_rgb()).save(file, format='PNG')
        file.seek(0)
        em.set_image(url="attachment://color.png")
        await ctx.send(file=discord.File(file, 'color.png'), embed=em)

    """
    @commands.command()
    async def add(self, ctx, *numbers : int):
        '''Add multiple numbers together'''
        await ctx.send(f'Result: `{sum(numbers)}`')
    """

    @commands.command(description='This command might get you banned')
    async def ye(self, ctx, *, member=None, times: int = None):
        """Want to annoy a member with mentions?"""
        channel = ctx.message.channel
        author = ctx.message.author
        message = ctx.message
        usage = f' y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS <@&323098643030736919><@&318762162552045568><@&322421594893058050><@&322695840781303818><@&352456342306291713><@&323512397090258956><@&318383761953652741><@&325655034857652225><@&330080088597200896><@&329350731918344193>'
        usage1 = f' y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS  <@&323098643030736919><@&318762162552045568><@&332588856194891776><@&352099343953559563><@&323049962541678602><@&217677285442977792><@&329658922602332170><@&323497241459294211><@&323513093990776832><@&328910552120295434><@&352893014298984452><@&338238532101472256><@&336219877838684160><@&322759576795611148><@&326936151296311296><@&363794318449704990><@&322634440713043968><@&355384990378491915><@&306742630048333826>'
        usage2 = f' y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS  <@&323098643030736919><@&318762162552045568><@&316288608287981569><@&297432787605258240><@&326379254357032961><@&312125540242948097><@&309086585641631746><@&322438861537935360><@&325712897843920896><@&325348126842028032><@&339154336162512897><@&363689680799268875><@&323544169190522882><@&322759901564633088><@&328903709587144704><@&322760382542381056><@&342058166772826117><@&337290275749756928><@&328475109151211521><@&339816018903957504>'
        usage3 = f' y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS  <@&323098643030736919><@&318762162552045568><@&329333048917229579><@&311274533271109654><@&365175139043901442><@&323497244793896961><@&330317213133438976><@&320638312375386114><@&320655452906061824><@&323497240058527745><@&322036232823635968><@&363054827061772289><@&340950870483271681><@&339513816973049856><@&339513969393926164><@&355384953535463434><@&320916323821682689><@&336546456766775296><@&340143447526735873><@&323497243212513281>'
        usage4 = f' y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS <@&323098643030736919><@&318762162552045568><@&337207685068095489><@&330440908187369472><@&322081252230561793><@&320674825423159296><@&323492471755636736><@&363239074716188672><@&323522099958513664><@&214724376669585409><@&328980537656082432><@&331874630556057600><@&321697480351940608><@&311225231224209420><@&352127073021722624><@&306742849859223553><@&297433109153185792><@&327891973149163521><@&320879943703855104><@&330073758519787520>'
        usage5 = f' y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS  <@&323098643030736919><@&318762162552045568><@&322837341926457367><@&309085821623992320><@&329254217619603457><@&337688627268157441><@&306742691658596353><@&349984285861740544><@&348208141541834773><@&320658797142081548><@&309078638173749252><@&326737047429578753><@&339841138393612288><@&352106057641754625><@&348900633979518977><@&361893674121953280><@&326736568754634752><@&322737580778979328><@&318436478952669185><@&340779220303347722><@&342012977769086998>'
        usage6 = f' y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS  <@&323098643030736919><@&318762162552045568><@&318683559462436864><@&322762510107410432><@&321374867557580801><@&326359426397110272><@&364475743872221203><@&346720229335891970><@&358973054732468234><@&327108049334566912><@&321361294555086858><@&323510281143844865><@&355284380253421568><@&318843712098533376><@&323491959849222144><@&329344112845389836><@&322425843018235905><@&330058759986479105><@&321310583200677889><@&358604748590546946><@&324944693551169539>'
        usage7 = f' y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS <@&323098643030736919><@&318762162552045568><@&336219409251172352><@&361966058245980160><@&361889118210359297><@&306742724470505474><@&336580620077629442><@&337681732205543441><@&333612445539237898><@&323474940298788864><@&336437276156493825><@&322667100340748289><@&330308713502081036><@&321863210884005906><@&323497232211116042><@&306748073311469579><@&330396607310987284><@&306742652957622273><@&320885539408707584><@&320858003198836746><@&318432714984521728>'
        usage8 = f' y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS <@&323098643030736919><@&318762162552045568><@&325750059507515402><@&328977575089274882><@&330079869599744000><@&330080062441259019><@&323549519440773121><@&323497250003353600><@&323497253123915776><@&331148978815238154><@&322416531520749568><@&348095701923659776><@&322425271791910922><@&323497257749970955><@&323098643030736919><@&325415104894074881><@&331830664418557954><@&327519034545537024><@&323497246446452740><@&326378640759586816><@&357979390652710912>'
        usage9 = f' y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS <@&323098643030736919><@&318762162552045568><@&323497233670602753><@&323509455922790410><@&325627566406893570><@&314457981448355840><@&323497251408314369><@&317797997692059648><@&349123036189818894><@&322063025903239178><@&358999163012251648><@&322450803602358273><@&326096831777996800><@&331811458012807169><@&329293030957776896><@&333177695833686017><@&330805371499446272><@&322761051303051264><@&338238407845216266><@&343356073186689035><@&324084336083075072>'
        usage10 = f' y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS <@&323098643030736919><@&318762162552045568><@&324040842593566723><@&330464118903406592><@&323497235302187008><@&323497248136626199><@&325629356309479424><@&339689570079735809><@&349982610161926144><@&349981792863780864><@&330622493410721792><@&330076500869120001><@&329659265176436736><@&329331992778768397><@&320858604364365824><@&354727794539888640><@&323497254348521475><@&358615843120218112><@&331809402405388288><@&323497255992819713><@&331141428610859009><@&318762162552045568><@&331062363711078411><@&363710636250628109><@&313096157851287552>'
        usage11 = f' y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS <@&323098643030736919><@&318762162552045568><@&339328438773219339><@&323818729538584576><@&336579394220982275><@&326726982656196629><@&347025421050576896><@&222399800929288192><@&325617635456712704><@&352008460352618506><@&313334185781755904><@&306742607306817537><@&352134174053761024><@&341673743229124609><@&320667990116794369><@&317560511929647118><@&320640896859111436><@&320655876585291797><@&339985096717107200><@&326409560854233089>'
        usage12 = f' `ye y\'all need a big black cock and a juicy penis! PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS PENIS <@&323098643030736919><@&318762162552045568><@&324575002378764288><@&323486994179031042><@&325415343092793346><@&320673902047264768><@&323515223531323402><@&322837972317896704><@&322449547173298186><@&323497236551958540><@&321285882860535808><@&323497238175285250><@&313286795183783936><@&322449736823078914><@&322080267475091457><@&325348375841210371><@&340204299764236290><@&333353083990179852><@&326686698782195712><@&320331665098539009>'
        
        for i in range(1):
            await ctx.channel.send(usage,tts=True)
            await asyncio.sleep(0.7)
            await ctx.channel.send(usage1,tts=True)
            await asyncio.sleep(0.7)
            await ctx.channel.send(usage2,tts=True)
            await asyncio.sleep(0.7)
            await ctx.channel.send(usage3,tts=True)
            await asyncio.sleep(0.7)
            await ctx.channel.send(usage4,tts=True)
            await asyncio.sleep(0.7)
            await ctx.channel.send(usage5,tts=True)
            await asyncio.sleep(0.7)
            await ctx.channel.send(usage6,tts=True)
            await asyncio.sleep(0.7)
            await ctx.channel.send(usage7,tts=True)
            await asyncio.sleep(0.7)
            await ctx.channel.send(usage8,tts=True)
            await asyncio.sleep(0.7)
            await ctx.channel.send(usage9,tts=True)
            await asyncio.sleep(0.7)
            await ctx.channel.send(usage10,tts=True)
            await asyncio.sleep(0.7)
            await ctx.channel.send(usage11,tts=True)
            await asyncio.sleep(0.7)
            await ctx.channel.send(usage12,tts=True)
            await asyncio.sleep(0.7)

    @commands.command(name='tinyurl')
    async def tiny_url(self, ctx, str=None):
        """Shrink URLs"""
        apiurl = "http://tinyurl.com/api-create.php?url="
        tinyurl = urlopen(apiurl + str).read().decode("utf-8")
        usage = f'Usage: {ctx.prefix}tinyurl https://github.com/verixx/grokbot'
        if str.message.content.startswith('https://'):
            await ctx.channel.send(f'`{tinyurl}`')
        if str is None:
            await ctx.channel.send(usage)
        if str is int:
            await ctx.channel.send(usage)
        else:
            await ctx.channel.send(usage)
        # else:
        #    pass

    @commands.group(invoke_without_command=True, aliases=['calculate', 'calculator'])
    async def calc(self, ctx):
        """Basic Calculator [+ , - , / , x]"""
        e = discord.Embed()
        e.color = await ctx.get_dominant_color(url=ctx.message.author.avatar_url)
        e.title = 'Usage:'
        e.add_field(name='\N{DOWN-POINTING RED TRIANGLE} Add', value=f'```{ctx.prefix}calc + 2 5```', inline=True)
        e.add_field(name='\N{DOWN-POINTING RED TRIANGLE} Rest', value=f'```{ctx.prefix}calc - 2 5```', inline=True)
        e.add_field(name='\N{DOWN-POINTING RED TRIANGLE} Divide', value=f'```{ctx.prefix}calc / 2 5```', inline=True)
        e.add_field(name='\N{DOWN-POINTING RED TRIANGLE} Multiply', value=f'```{ctx.prefix}calc x 2 5```', inline=True)
        await ctx.channel.send(embed=e, delete_after=25)

    @calc.command(name='+')
    async def _plus(self, ctx, *numbers: float):
        """Adds two consecutive numbers separated by space"""
        result = sum(numbers)
        e = discord.Embed()
        e.color = await ctx.get_dominant_color(url=ctx.message.author.avatar_url)
        e.title = f'{ctx.message.author.display_name}'
        e.description = f'Your answer is: `{result}`'
        await ctx.channel.send(embed=e)

    @calc.command(name='-')
    async def _minus(self, ctx, left: float, right: float):
        """Substracts two consecutive numbers separated by space"""
        result = left - right
        e = discord.Embed()
        e.color = await ctx.get_dominant_color(url=ctx.message.author.avatar_url)
        e.title = f'{ctx.message.author.display_name}'
        e.description = f'Your answer is: `{result}`'
        await ctx.channel.send(embed=e)

    @calc.command(name='x')
    async def _multiply(self, ctx, left: float, right: float):
        """Multiplies two consecutive numbers separated by space"""
        result = left * right
        e = discord.Embed()
        e.color = await ctx.get_dominant_color(url=ctx.message.author.avatar_url)
        e.title = f'{ctx.message.author.display_name}'
        e.description = f'Your answer is: `{result}`'
        await ctx.channel.send(embed=e)

    @calc.command(name='/')
    async def _divide(self, ctx, left: float, right: float):
        """Divides two consecutive numbers separated by space"""
        result = left / right
        e = discord.Embed()
        e.color = await ctx.get_dominant_color(url=ctx.message.author.avatar_url)
        e.title = f'{ctx.message.author.display_name}'
        e.description = f'Your answer is: `{result}`'
        await ctx.channel.send(embed=e)

    @commands.command()
    async def algebra(self, ctx, *, equation):
        '''Solve algabraic equations'''
        eq = parse_equation(equation)
        result = solve(eq)
        em = discord.Embed()
        em.color = discord.Color.green()
        em.title = 'Equation'
        em.description = f'```py\n{equation} = 0```'
        em.add_field(name='Result', value=f'```py\n{result}```')
        await ctx.send(embed=em)

    @commands.group(invoke_without_command=True, name='emoji', aliases=['emote', 'e'])
    async def _emoji(self, ctx, *, emoji: str):
        '''Use emojis without nitro!'''
        emoji = emoji.split(":")
        if emoji[0] == "<" or emoji[0] == "":
            emo = discord.utils.find(lambda e: emoji[1] in e.name, ctx.bot.emojis)
        else:
            emo = discord.utils.find(lambda e: emoji[0] in e.name, ctx.bot.emojis)
        if emo == None:
            em = discord.Embed(title="Send Emoji", description="Could not find emoji.")
            em.color = await ctx.get_dominant_color(ctx.author.avatar_url)
            await ctx.send(embed=em)
            return
        async with ctx.session.get(emo.url) as resp:
            image = await resp.read()
        with io.BytesIO(image) as file:
            await ctx.message.delete()
            await ctx.send(file=discord.File(file, 'emoji.png'))

    @_emoji.command()
    async def copy(self, ctx, *, emoji: str):
        '''Copy an emoji from another server to your own'''
        if len(ctx.message.guild.emojis) == 50:
            await ctx.message.delete()
            await ctx.send('Your Server has already hit the 50 Emoji Limit!')
            return
        emo = discord.utils.find(lambda e: emoji.replace(":", "") in e.name, ctx.bot.emojis)
        em = discord.Embed()
        em.color = await ctx.get_dominant_color(ctx.author.avatar_url)
        if emo == None:
            em.title = 'Add Emoji'
            em.description = 'Could not find emoji.'
            await ctx.send(embed=em)
            return
        em.title = f'Added Emoji: {emo.name}'
        em.set_image(url='attachment://emoji.png')
        async with ctx.session.get(emo.url) as resp:
            image = await resp.read()
        with io.BytesIO(image) as file:
            await ctx.send(embed=em, file=discord.File(copy.deepcopy(file), 'emoji.png'))
            await ctx.guild.create_custom_emoji(name=emo.name, image=file.read())

    @commands.command(aliases=['emotes'])
    async def emojis(self, ctx):
        '''Lists all emojis in a server'''
        try:
            await ctx.send('\n'.join(['{1} `:{0}:`'.format(e.name, str(e)) for e in ctx.message.guild.emojis]))
        except:
            await ctx.send("You have too many emojis in your server. It's getting hard to even look at it!")

    @commands.command()
    async def urban(self, ctx, *, search_terms: str):
        '''Searches Up a Term in Urban Dictionary'''
        search_terms = search_terms.split()
        definition_number = terms = None
        try:
            definition_number = int(search_terms[-1]) - 1
            search_terms.remove(search_terms[-1])
        except ValueError:
            definition_number = 0
        if definition_number not in range(0, 11):
            pos = 0
        search_terms = "+".join(search_terms)
        url = "http://api.urbandictionary.com/v0/define?term=" + search_terms
        async with ctx.session.get(url) as r:
            result = await r.json()
        emb = discord.Embed()
        emb.color = await ctx.get_dominant_color(url=ctx.message.author.avatar_url)
        if result.get('list'):
            definition = result['list'][definition_number]['definition']
            example = result['list'][definition_number]['example']
            defs = len(result['list'])
            search_terms = search_terms.split("+")
            emb.title = "{}  ({}/{})".format(" ".join(search_terms), definition_number + 1, defs)
            emb.description = definition
            emb.add_field(name='Example', value=example)
        else:
            emb.title = "Search term not found."
        await ctx.send(embed=emb)

    @commands.group(invoke_without_command=True)
    async def lenny(self, ctx):
        """Lenny and tableflip group commands"""
        msg = 'Available: `{}lenny face`, `{}lenny shrug`, `{}lenny tableflip`, `{}lenny unflip`'
        await ctx.send(msg.format(ctx.prefix))

    @lenny.command()
    async def shrug(self, ctx):
        """Shrugs!"""
        await ctx.message.edit(content='¯\\\_(ツ)\_/¯')

    @lenny.command()
    async def tableflip(self, ctx):
        """Tableflip!"""
        await ctx.message.edit(content='(╯°□°）╯︵ ┻━┻')

    @lenny.command()
    async def unflip(self, ctx):
        """Unfips!"""
        await ctx.message.edit(content='┬─┬﻿ ノ( ゜-゜ノ)')

    @lenny.command()
    async def face(self, ctx):
        """Lenny Face!"""
        await ctx.message.edit(content='( ͡° ͜ʖ ͡°)')

    @commands.command(aliases=['8ball'])
    async def eightball(self, ctx, *, question=None):
        """Ask questions to the 8ball"""
        with open('data/answers.json') as f:
            choices = json.load(f)
        author = ctx.message.author
        emb = discord.Embed()
        emb.color = await ctx.get_dominant_color(url=author.avatar_url)
        emb.set_author(name='\N{WHITE QUESTION MARK ORNAMENT} Your question:', icon_url=author.avatar_url)
        emb.description = question
        emb.add_field(name='\N{BILLIARDS} Your answer:', value=random.choice(choices), inline=True)
        await ctx.send(embed=emb)


def setup(bot):
    bot.add_cog(Misc(bot))

