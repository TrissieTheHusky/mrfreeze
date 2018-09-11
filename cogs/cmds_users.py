import discord, re, datetime
from discord.ext import commands
from botfunctions import native, checks, userdb

class RulesCog():
    def __init__(self, bot):
        self.bot = bot

    async def on_ready(self):
        # Creating dict of all the region role ids
        self.region_ids = dict()
        for guild in self.bot.guilds:
            self.region_ids[guild.id] = {
            'Africa':           discord.utils.get(guild.roles, name='Africa'),
            'North America':    discord.utils.get(guild.roles, name='North America'),
            'South America':    discord.utils.get(guild.roles, name='South America'),
            'Asia':             discord.utils.get(guild.roles, name='Asia'),
            'Europe':           discord.utils.get(guild.roles, name='Europe'),
            'Middle East':      discord.utils.get(guild.roles, name='Middle East'),
            'Oceania':          discord.utils.get(guild.roles, name='Oceania'),
            'Antarctica':       discord.utils.get(guild.roles, name='Antarctica')
            }

    @commands.command(name='rules', aliases=['rule'])
    async def _rules(self, ctx, *args):
        request = str()
        for i in args:
            request += (i.lower())

        rules = {
        1: ( '1', 'topic', 'ontopic', 'offtopic' ),
        2: ( '2', 'civil', 'disagreement' ),
        3: ( '3', 'dismissive', 'opinion', 'opinions' ),
        4: ( '4', 'joke', 'jokes', 'joking', 'sex', 'sexual',
             'orientation', 'weight', 'race', 'skin', 'color',
             'gender', 'colour' ),
        5: ( '5', 'shoe', 'shoes', 'age', 'mature', 'maturity', 'shoesize', 'act' ),
        6: ( '6', 'spam' ),
        7: ( '7', 'benice', 'nice' )
        }

        called_rules = list()

        # If 'all' is in the request we'll just call all rules.
        # If not we'll see if any of the keywords are in the request.
        if 'all' in request:
            called_rules = [ 1, 2, 3, 4, 5, 6, 7 ]
        else:
            for rule_no in rules:
                for keyword in rules[rule_no]:
                    if keyword in request and rule_no not in called_rules:
                        called_rules.append(rule_no)

        if len(called_rules) == 0:
            await ctx.send('Sorry %s, your terms don\'t seem to match any rules. :thinking:' % (ctx.author.mention,))
        else:
            await ctx.send(ctx.author.mention + '\n' + native.get_rule(called_rules))

    @commands.command(name='mrfreeze', aliases=['freeze'])
    async def _mrfreeze(self, ctx, *args):
        # If they're asking for help, we'll default to the help_reply.
        pls_help = ('help', 'wtf', 'what', 'what\'s', 'wut', 'woot')
        help_reply = False
        for i in pls_help:
            if i in args:
                help_reply = True

        # If they say the bot sucks, we'll default to the suck_reply.
        you_suck = ('sucks', 'suck', 'blows', 'blow')
        suck_reply = False
        for i in you_suck:
            if i in args:
                suck_reply = True

        # If they're telling the bot to kill itself... well...
        death_reply = False
        passive_die = ('die', 'suicide')
        for i in args:
            if i in passive_die:
                death_reply = True

        active_die  = ('kill', 'murder', 'destroy')
        yourself_spells = ('yourself', 'urself', 'uself', 'u', 'you')
        for i in active_die:
            for k in yourself_spells:
                if i and k in args:
                    death_reply = True

        if help_reply:
            await ctx.send('Allow me to break the ice: My name is Freeze and ' +
            'the command **!mrfreeze** will have me print one of my timeless quotes from Batman & Robin.')
        elif suck_reply:
            await ctx.send('Freeze in hell, ' + ctx.author.mention + '!')
        elif death_reply:
            await ctx.send(ctx.author.mention + ' ' +
            'You\'re not sending ME to the COOLER!')
        else:
            quote = native.mrfreeze()
            quote = quote.replace('Batman', ctx.author.mention)
            quote = quote.replace('Gotham', '**' + ctx.guild.name + '**')
            await ctx.send(quote)

    @commands.command(name='vote', aliases=['election', 'choice', 'choose'])
    async def _vote(self, ctx, *args):
        remoji = re.compile('<:\w+:\d+>')
        remojid = re.compile('\d+')
        # skipping first line because we don't need it
        lines = ctx.message.content.split()[1:]

        # For each line we'll try to add a react of the first character,
        # if that fails we'll look for a custom emoji of the form:
        # <:\w+:\d+> (remoji)

        success = False
        for line in lines:
            try:
                await ctx.message.add_reaction(line[0])
                success = True
            except:
                pass

            match = remoji.match(line)
            if not isinstance(match, type(None)):
                match_id = int(remojid.search(match.group()).group())
                emoji = discord.utils.get(ctx.guild.emojis, id=match_id)
                try:
                    await ctx.message.add_reaction(emoji)
                    success = True
                except:
                    pass

        if success:
            await ctx.send('%s That\'s such a great proposition I voted for everything!' % (ctx.author.mention))
        else:
            await ctx.send('%s There\'s literally nothing I can vote for in your smuddy little attempt at a vote! :rofl:' % (ctx.author.mention,))

    @commands.command(name='region', aliases=['regions'])
    async def _region(self, ctx, *args):
        region_ids = self.region_ids
        # List of regions
        regions = {
        'Africa':        ('africa',),
        'North America': ('north america', 'usa', 'united states', 'canada', 'mexico', 'us', 'na'),
        'South America': ('south america', 'argentina', 'brazil', 'chile', 'peru', 'sa'),
        'Asia':          ('asia', 'china', 'taiwan', 'japan', 'nihon', 'nippon', 'korea'),
        'Europe':        ('europe', 'great britain', 'france', 'united kingdom', 'gb', 'uk',
                          'sweden', 'denmark', 'norway', 'finland', 'scandinavia', 'poland',
                          'italy', 'germany', 'russia', 'spain', 'portugal', 'hungary'),
        'Middle East':   ('middle east', 'middle-east', 'mesa', 'ksa', 'saudi'),
        'Oceania':       ('oceania', 'australia', 'zealand', 'zeeland')
        }

        ### See if the user wants to blacklist someone
        add_blacklist_alias = ('blacklist', 'black', 'bl', 'ban', 'forbid')
        rmv_blacklist_alias = ('unblacklist', 'unblack', 'unbl', 'unban', 'unforbid', 'allow', 'remove')

        add_blacklist = False
        rmv_blacklist = False
        for alias in add_blacklist_alias:
            if (' ' + alias) in ctx.message.content:
                add_blacklist = True

        for alias in rmv_blacklist_alias:
            if (' ' + alias) in ctx.message.content:
                rmv_blacklist = True

        ### See if the user wants a list of regions
        list_regions = ('list', 'regions', 'available')
        give_list = False
        for alias in list_regions:
            if (' ' + alias) in ctx.message.content:
                give_list = True

        ### See if the user mentioned antarctica.
        antarctica_choice = False
        antarctica_spelling = False
        antarctica = ('antarctica', 'antarctic', 'antartica', 'anctartctica', 'antartic', 'anarctica')
        spelling = ''
        for alias in antarctica:
            if (' ' + alias + ' ') in (ctx.message.content.lower() + ' '):
                antarctica_choice = True
                if (alias != 'antarctica') and (alias != 'antarctic'):
                    antarctica_spelling = True
                    spelling = alias
        if not antarctica_spelling:
            spelling = 'antarctic(a)'

        ### See if the user is a mod, if they're not see if they're blacklisted.
        is_mod = await checks.is_mod(ctx, no_error=True)
        if not is_mod:
            is_blacklisted = userdb.is_blacklisted(ctx.author)
        else:
            is_blacklisted = False

        # Now we'll execute our command.
        # Only one command will be executed and they will be executed in
        # in the following order:
        # - antarctica
        # - conflicting blacklist (if we have both)
        # - remove blacklist
        # - add blacklist,
        # - block user due to blacklisting
        # - list regions
        # - assign a region

        if antarctica_choice:
            if antarctica_spelling:
                # 20 minutes for incorrect spelling.
                end_time = datetime.datetime.now() + datetime.timedelta(minutes=20)
            else:
                # 10 minutes for correct spelling.
                end_time = datetime.datetime.now() + datetime.timedelta(minutes=10)

            # Adding the user to is_muted table. This action is not voluntary.
            # fix_mute(user, voluntary=False, until=None, delete=False)
            success, reason = userdb.fix_mute(ctx.author, until=end_time)

            if success:
                # First thing to do if the mute table was updated successfull is to add the actual role.
                try:
                    await ctx.author.add_roles(self.region_ids[ctx.guild.id]['Antarctica'], reason=('User issued !region ' + spelling))
                except discord.Forbidden:
                    success = False
                    reason = ('Lacking permissions to change role.')
                except discord.HTTPException:
                    success = False
                    reason = ('Error connecting to discord.')

            if success:
                if not antarctica_spelling:
                    # Correct spelling.
                    await ctx.send(ctx.author.mention + ' is a filthy smud claiming to live in Antarctica, ' +
                                  'their wish has been granted and they will be stuck there for about TEN minutes!')

                else:
                    await ctx.send(ctx.author.mention + ' is a filthy smud claiming to live in \'' + spelling + '\'! They couldn\'t even spell it right ' +
                                   'and because of that they\'ll be stuck there for about TWENTY minutes!')

            elif not success:
                await ctx.send(ctx.author.mention + ' is a filthy smud claiming to live in Antarctica, but I couldn\'t banish them there due to:\n' + reason)

        elif add_blacklist or rmv_blacklist:
            if not is_mod:
                # If the user is not mod, they're not allowed to touch the blacklist.
                # This will earn them 15 minutes in Antarctica.
                end_time = datetime.datetime.now() + datetime.timedelta(minutes=15)
                success, reason = userdb.fix_mute(ctx.author, until=end_time)
                if success:
                    try:
                        await ctx.author.add_roles(self.region_ids[ctx.guild.id]['Antarctica'], reason=('User issued !region ' + spelling))
                    except discord.Forbidden:
                        success = False
                        reason = ('Lacking permissions to change role.')
                    except discord.HTTPException:
                        success = False
                        reason = ('Error connecting to discord.')

                if success:
                    await ctx.send(ctx.author.mention + ' Smuds like you are not allowed to neither remove nor add entries to the blacklist. ' +
                                   'This misdemeanor has earned you about FIFTEEN minutes in Antarctica!')
                else:
                    await ctx.send(ctx.author.mention + ' Smuds like you are not allowed to neither remove nor add entries to the blacklist.\n\n' +
                                   'Normally this would earn you FIFTEEN minutes in Antarctica, but I failed to banish you due to:\n' + reason)

            elif add_blacklist and rmv_blacklist:
                # Conflicting messages, not sure if we're supposed to add or remove.
                await ctx.send(ctx.author.mention + ' I\'m getting mixed messages, I\'m not sure if you want to remove or add entries to the blacklist.')

            elif len(ctx.message.mentions) == 0:
                # We can't do this without any mentions.
                await ctx.send(ctx.author.mention + ' You want to edit the blacklist, but you failed to mention anyone. ' +
                               'You\'re a huge disappointment to modkind, please never talk to me again.')

            else:
                # Else means that:
                # - we have add_blacklist or rmv_blacklist but not both.
                # - user is mod.
                # - at least one person was mentioned.

                # userdb.fix_blacklist takes the boolean argument 'add'
                # to know if it's gonna add or delete entries.
                if add_blacklist:
                    action = True
                else:
                    action = False

                # Who was added and who wasn't?
                list_of_fails = list()
                list_of_successes = list()

                for user in ctx.message.mentions:
                    success, blacklisted = userdb.fix_blacklist(user, add=action)
                    if success:
                        list_of_successes.append(user)
                    else:
                        list_of_fails.append(user)

                fails_tally = len(list_of_fails)
                total_tally = len(ctx.message.mentions)
                fails_str = native.mentions_list(list_of_fails)
                success_str = native.mentions_list(list_of_successes)

                if add_blacklist:
                    if total_tally == 1 and fails_tally == 0:
                        # One total and succeeded.
                        await ctx.send('%s The filthy region abusing smud %s has been banned from changing their region.' % (ctx.author.mention, success_str))

                    elif total_tally == 1 and fails_tally == 1:
                        # One total and failed.
                        await ctx.send('%s I wasn\'t able to add %s to the list of smuds banned from changing their region. Perhaps they\'re already on the list?' % (ctx.author.mention, fails_str))

                    elif total_tally > 1 and fails_tally == 0:
                        # More than one and all succeeded.
                        await ctx.send('%s The filthy region abusing smuds %s have been banned from changing their region.' % (ctx.author.mention, success_str))

                    elif total_tally > 1 and fails_tally > 0:
                        # More than one and at least one fail.
                        await ctx.send('%s I wasn\'t able to add all of the requested users to the list of smuddy region abusers, perhaps some of them were already there?\nBlacklisted: %s\nNot blacklisted: %s' % (ctx.author.mention, success_str, fails_str))

                elif rmv_blacklist:
                    if total_tally == 1 and fails_tally == 0:
                        # One total and succeeded.
                        await ctx.send('%s The user %s is once again allowed to change their region.' % (ctx.author.mention, success_str))

                    elif total_tally == 1 and fails_tally == 1:
                        # One total and failed.
                        await ctx.send('%s I wasn\'t able to remove %s from the list of smuds banned from changing their region. Perhaps they\'re already off the list?' % (ctx.author.mention, fails_str))

                    elif total_tally > 1 and fails_tally == 0:
                        # More than one and all succeeded.
                        await ctx.send('%s The users %s are once again allowed to change their regions.' % (ctx.author.mention, success_str))

                    elif total_tally > 1 and fails_tally > 0:
                        # More than one and at least one fail.
                        await ctx.send('%s I wasn\'t able to remove all of the requested users from the list of smuddy region abusers, perhaps some of them were already removed?\nUnblacklisted: %s\nNot unblacklisted: %s' % (ctx.author.mention, success_str, fails_str))

        elif is_blacklisted:
            await ctx.send('%s Smuds like you are why we can\'t have nice things, or rather... why you can\'t have nice things. The *privilege* of changing your own region has been revoked from you.' % (ctx.author.mention))

        elif give_list:
            # Print a list of all the available regions.
            await ctx.send(ctx.author.mention + ' The available regions are:\n' +
                           '- Africa\n' +
                           '- North America\n' +
                           '- South America\n' +
                           '- Antarctica\n' +
                           '- Asia\n' +
                           '- Europe\n' +
                           '- Middle-East\n' +
                           '- Oceania')

        else:
            # List of region_ids from role abc's in region_ids[guild.id], except for Antarctica.
            region_ids = [ self.region_ids[ctx.guild.id][region].id for region in self.region_ids[ctx.guild.id] if region != 'Antarctica' ]
            # Author role ids minus the ones in region_ids
            old_author_roles = [ i.id for i in ctx.author.roles ]
            new_author_roles = [ i.id for i in ctx.author.roles if i.id not in region_ids ]

            match = list()
            for region in regions:
                for alias in regions[region]:
                    if (' ' + alias + ' ') in (ctx.message.content.lower() + ' '):
                        match = [region, self.region_ids[ctx.guild.id][region].id]

            if len(match) == 0:
                await ctx.send('%s I couldn\'t find any match for the region you mentioned. Type !region list for a list of available regions.' % (ctx.author.mention,))

            elif match[1] in old_author_roles:
                await ctx.send('%s You\'re already in %s, wtf are you trying to do?' % (ctx.author.mention, match[0]))

            else:
                new_author_roles.append(match[1])

                for i in range(len(new_author_roles)):
                    new_author_roles[i] = discord.Object(id = new_author_roles[i])

                try:
                    await ctx.author.edit(roles=new_author_roles)
                    await ctx.send('%s You\'ve successfully been assigned a new region!\nWelcome to **%s**!' % (ctx.author.mention, match[0]))
                except discord.Forbidden:
                    await ctx.send('%s I found a match for you, but I wasn\'t allowed to edit your roles due to insufficient privilegies. :sob:' % (ctx.author.mention,))
                except discord.HTTPException:
                    await ctx.send('%s I found a match for you, but due to a connection error I wasn\'t able to edit your roles. :sob:' % (ctx.author.mention,))


def setup(bot):
    bot.add_cog(RulesCog(bot))