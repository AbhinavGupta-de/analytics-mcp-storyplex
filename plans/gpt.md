# **Market Landscape of Online Fiction**

The global **Internet literature** market – encompassing fanfiction, web novels, manga/comics, etc. – is rapidly expanding.  A recent analysis values this market at ~$10.2 billion in 2024 and projects it will reach ~$25.6 billion by 2033 (CAGR ~9.4%)  .  This growth is fueled by digital self-publishing (Amazon Kindle, Wattpad, Webnovel), increased mobile access, and fan communities on social media  .  Fanfiction is explicitly cited as a significant driver, as fans create vast libraries of free content on platforms like AO3 and FanFiction.net .  Notably, **Asia-Pacific** leads globally (owning ~30% of market share) , and genres like romance dominate digital comics/webtoons (≈39% share) .

**Key trend:**  Mobile-first platforms (vertical scrolling webtoons, mobile apps) and creator-driven revenue (ad-sharing, crowdfunding) are fueling expansion .  For example, the **Webtoons** market alone was $10.85 B in 2025 and is forecast to soar to $71.4 B by 2032 (≈30% annual growth) .

This graphic illustrates webtoon market growth (source: Persistence Market Research ).  Similarly, fanfiction sites see continual traffic growth: Archive of Our Own (AO3) now outpaces Wattpad, ranking ~#140 globally vs Wattpad’s #299  and #1 vs #4 in US Books/Lit category .  By contrast, FanFiction.net has declined (global rank ~#1574 in Nov 2025 ).  Together, these trends underscore huge reader communities: AO3 reportedly sees hundreds of millions of visits per month , Wattpad tens of millions, and RoyalRoad (an English web-fiction site) ~14 M visits in Feb 2025 .

![image.png](attachment:d307abca-b224-4861-82a8-d3009dacb43b:image.png)

## **Fanfiction Platforms and Data Fields**

**Major sites:**  Archive of Our Own (AO3) and FanFiction.net are the largest English-language fanfic archives.  Wattpad also hosts fanfiction alongside original works, especially for younger readers.  Non-English fanfic communities (e.g. in Chinese, Spanish) exist but AO3/FFN cover most Western fandoms.

- **AO3:** A non-profit archive (CC BY-NC-SA) with tens of millions of works. Most visited in the US . AO3 provides rich metadata per story: fandom(s), sub-fandoms, rating, relationships (pairings), characters, tags, language, publication/update dates, chapter count and word count, plus engagement stats (hits/views, comments, kudos/likes, bookmarks/favorites) . These fields (see example snippet ) would be stored for each work. AO3 can be scraped using community tools (e.g. the unofficial ao3 Python library ) or by HTML parsing (the site has been partially open about building an official API, but it’s not public yet).
- **FanFiction.net:** An older archive with global rank ~#1574 . It displays rating, categories, characters, and stats: words, chapters, reviews, favorites, follows, and date information. Unlike AO3, FFN uses “favorites/follows” instead of bookmarks, and “reviews” instead of comments. Data fields to collect mirror AO3: fandom (category), tags, relationships (if any), language, rating, words, chapters, reviews, favorites, follows, and publication dates. (FFN has no official API, so scraping or light-weight bots are needed.)
- **Wattpad:** A large platform for original and fan fiction. According to SimilarWeb, Wattpad remains a top site (global rank #299 ). Wattpad offers a **public API (v4)** for story data . For example, a search API call returns JSON with readCount and voteCount for each story . Wattpad stories include fields like language, tags, parts (chapters), votes/likes, and read/view count. The plan should include using Wattpad’s developer API (with authentication) to retrieve read/vote stats for top stories and authors.
- **RoyalRoad:** A major English web-novel site (14 M visits Feb 2025 ). Primarily hosts original fiction (often fantasy/like LitRPG). Most works are ongoing, with authors largely supported by Patreon. RoyalRoad’s data (titles, genres, views, followers, Patrons, etc.) can be scraped; there is no official public API. Analyses show its users are ~70% male aged 18–30 and that “big four” genres (Fantasy, Adventure, Action, Magic) dominate views . We would capture title, author, tags, chapters/words, view and follow counts, and Patreon-linked earnings for top works.

**Popular content & tags:**  On AO3, the top subject is **“Real Person Fiction”** (fanfic about celebrities, historical figures) ; romance and adventure are the most common fanfic subgenres .  Fandom-specific tags (e.g. “Harry Potter”, “Marvel Cinematic Universe”, “Twilight”) should be recorded to identify the most popular universes.  Tracking tag hierarchies (main vs additional tags) will help classify themes and tropes.  Also record rating (e.g. Teen/Adult), warnings (e.g. Underage, Violence), and K/C/T (Kid/Teen/Explicit) to gauge maturity levels.

**Engagement metrics:**  For each story, store *chapter count*, *words per chapter* (if needed), *total words*, *views/hits*, *likes/kudos*, *bookmarks/favorites*, *comments/reviews*, and *publish/update dates*.  This enables later analysis of “most-read” works, typical lengths, update frequency, etc.  Also capture author info (username, number of works, possible creator career info).  For AO3 specifically, the example shows one can fetch all these stats automatically .  Ultimately, we aim to identify the *top N works per genre/fandom* (by words, hits, kudos, etc.) and analyze their features (length, themes, pairings, etc.).

## **Web Novels and Light Novel Platforms**

**Major sites:**  Beyond fanfic, *web novels* (often serialized original stories) and *light novels* (East Asian-style fiction) have huge followings. Key platforms include:

- **Webnovel (Inkstone)**: A Tencent-owned site for Chinese-origin (and original English) serials. Writers must contract; earnings come via wordcount and reader unlocks . Popular English genres include fantasy (cultivation/system novels), urban fantasy, romance, CEO drama, etc . We would gather novel metadata (title, author, genre, language, contract status) and reader engagement (page reads, coins spent on premium chapters if accessible). The medium suggests top writers earn ~$500–2,000+/month from such models , indicating which titles are most lucrative.
- **Wattpad (original fiction)**: Wattpad also hosts original (non-fanfic) novels by amateur authors. Data fields: title, tags/genres, language, reads, votes, comments, parts, and author info. Many Wattpad authors monetize via the “Paid Stories” program (readers pay coins to unlock chapters) or by using Wattpad premium (ad revenue share).
- **RoyalRoad (see Fanfiction)**: Although originally for web novels, RoyalRoad is mostly original fiction now. Top works often get collected into books or spin-offs. We would track RoyalRoad series that have moved to Kindle/Patreon (as identified by e.g. story descriptions).
- **WuxiaWorld, Gravity Tales, etc.:** Popular for English translations of Chinese web novels (martial arts & fantasy). If relevant to our users, consider scraping data from such forums (though official data may be minimal).
- **Light Novels (Japanese/Other)**: Official translated light novels are sold (Kindle, BookWalker), but fan-translations exist on sites like Baka-Tsuki (now defunct) or user blogs. For market analysis, focus on platforms where user feedback exists (e.g. number of ratings on Amazon for top light novels). Also track **Pixiv**/**Shousetsuka ni Narou** for original Japanese web-novels.

**Data focus:**  For web novels/light novels, gather series-level info: genre tags, chapter/word counts, update frequency, language.  Engagement varies: e.g. RoyalRoad shows views and followers; Webnovel shows subscriber counts and review counts; Wattpad shows reads/votes.  We should also capture **creator platforms** (author blogs, Patreon/Ko-fi links) and any reported earnings (if public). Many web-novel authors list Patreon or sell print volumes.  For example, one Webnovel analysis noted that **new authors often earn ~$100–300/month**, active writers $500–1200, and top $2K+ .  This demonstrates the scale: only a few authors make significant revenue, while many are at the hobby level.

## **Manga/Manhua and Webtoon Platforms**

**Major platforms:**  Digital comic consumption is split between manga/manhwa and webtoons:

- **Webtoon (Naver/Line Webtoon):** The largest global webtoon platform. No public scraping API, but data can be scraped from the site or via unofficial means. Creators can earn via ad-sharing and “Pass” purchases. Webtoon’s terms allow creators to share ad revenue (though details are not public). The market report notes Webtoon’s enormous user base driving the $10.85 B market .
- **Tapas:** Another webcomic platform (owned by Kakao). Offers ads, microtransactions (Ink), and premium series. We should capture title, genre, page/chapter count, and metrics like subscribers/reads if visible. (Tapas has an internal artist portal but no open API.)
- **MangaDex:** A volunteer-run aggregator of manga/manhwa. It has an open API (v5) that can provide metadata on titles (languages, chapters, views, follows). We should use the **MangaDex API** to fetch top series by follows or views, along with chapter counts per series. Since user asked for manga/manhua as well, MangaDex covers Japanese/Korean/Chinese comics in multiple languages.
- **Other official sources:** Crunchyroll Manga, Shonen Jump+, MangaPlus (Shueisha) – these have official apps but limited web data. We can at least list their top titles from rankings if available. For example, MangaPlus ranks top weekly Shonen Jump chapters. Similarly, Tapas/Line Webtoon publish “rankings” on their site that could be scraped.

**Data to collect:**  For each comic/webtoon, record series title, original language, genre tags, chapter count, pages per chapter (if needed for word estimate), and popularity metrics: e.g. Webtoon shows total views and “Favorites” for each episode, Tapas shows subscribers.  MangaDex provides views, follows, ratings per chapter.  Also track ongoing vs completed status.  Top series by metrics can be identified (e.g. ‘Tower of God’, ‘Lore Olympus’, etc. on Webtoon; ‘Solo Leveling’ on Webtoon, etc.) and their authors’ earnings (some high-profile WEBTOON Creator leaders reportedly earn $300–$20K+/month via Patreon ).

This sector’s growth is huge: the *global webtoons market* will see triple-digit growth rates.  The report highlights Asia Pacific as the largest region (30.9% share) and romance as a dominant genre (39.4% share) .  Webtoon Entertainment and similar platforms actively expand content (e.g. licensing Marvel/Star Wars) .  Our database should include languages (many are Korean or Chinese originals), and platform-specific metrics for multi-language reach.

## **Creator Monetization and Trends**

**Revenue models:**  In all these spaces, creators typically rely on a mix of income streams: platform ads/crowdfunding, direct fan support (Patreon/Ko-fi), merchandise, and traditional publishing deals (paper books, comics, adaptations).  Key points:

- *Ad revenue & virtual purchases*: Platforms like Webtoon (Canvas) share ad revenue with creators . Wattpad’s Paid Stories pay per read (coins) and stipends. Tapas and similar pay via ad revenue and its own microtransaction system.
- *Crowdfunding*: Many writers run Patreon or Ko-fi. However, most authors earn modest sums. For example, one analysis noted **thousands** of fiction writers on Patreon but only ~25 earn >$1k/month . Another study of RoyalRoad found top 1% authors earn around $8K/month via Patreon , but most creators earn far less. (This implies broad creator base but few high-earners.)
- *Merch & licensing*: Successful fanfic writers sometimes publish original novels or sell art/merch. Many web novel authors eventually publish through Amazon Kindle or have their works adapted (e.g. local webnovels turned into anime). For example, one Patreon thread notes web-novel authors with 3k–14k patrons at $1+/month tiers (roughly $3k–$14k/mo) , often associated with web fiction on RoyalRoad/Webnovel.

**Trends:**  The landscape is shifting toward **AI tools** for writing and translation, and more “creator-first” platforms.  Reports mention emerging trends like AI-assisted writing tools, interactive storytelling, and blockchain for IP .  Also, reader rewards and tipping models are growing .  In webcomics, popular series are adapted into games, dramas, or anime, further boosting author visibility (e.g. *Lore Olympus* animated series, *Lore Olympus* had webtoon peaks).

Understanding earnings:  We must gather available data (Patreon pages, platform dashboards, news articles) to model income.  For instance, Webnovel contracts are typically $30–50 per 1,000 words , plus bonuses.  High-volume writers (80k–150k words/month) report ~$500–$1200 , while top authors exceed $2,000/month.  In practice, one could pull available public info on top creator earnings (some top web novelists discuss income online).  Although this analysis is “future work”, our plan is to ensure the database can correlate popularity metrics with monetization (e.g. linking a story to its author’s Patreon earnings when known).

## **Data Collection and Analytics Plan**

**Scope of data:**  We will build a unified database containing **works** from across platforms, with the following key fields (per item):

- **Identifier:** Story ID, title, author.
- **Platform & Language:** Source site (AO3, FFN, Wattpad, Webtoon, etc.) and content language.
- **Metadata:** Fandom (for fanfic) or genre tags, rating categories (age/explicitness), relationships/pairings, characters.
- **Structure:** Number of chapters, words (total and per chapter), publication date, last update.
- **Engagement:** Views/reads/hits, likes/kudos/votes, comments/reviews count, bookmarks/favorites, subscriber count (if applicable).
- **Creators:** Author’s profile info (may include total number of works, fan following, linked Patreon/Kofi if public).
- **Monetization cues:** Any available earnings or patronage data (e.g. Patreon pages, reward programs). Possibly an “earning” field if known.

All data should be timestamped to allow trend analysis (e.g. monthly snapshots of hit counts).  We’ll normalize metrics (some sites count differently) for cross-comparison (e.g. note that Wattpad’s “reads” vs AO3’s “hits” are roughly analogous).

**Sources & Methods:**  The plan is to scrape or use APIs for each platform:

- **AO3:** Use the unofficial Python library or custom scraper to crawl public pages. AO3’s robots.txt is permissive of read-only scraping. Respect rate limits. There’s no formal API yet, but libraries like ao3 (see [42]) show how to extract all needed fields. We might consider an offline download (AO3 allows archive download for CC works but that’s only content, not stats).
- **FanFiction.net:** Write a scraper to parse HTML. FFN has lists of works by fandom which can be iterated. Key challenge is it paginates listings; we can script through them. (Note: FFN often breaks stories into 5-chunk pages; ensure scraping all chapters if needed.)
- **Wattpad:** Apply for and use Wattpad’s API (story search, user libraries). For large-scale, a combination of API calls and light scraping might be needed (limit calls to avoid bans). APIs can give reads/votes; basic story info (title, tags) is also available via their developer API.
- **RoyalRoad:** Scrape directly (the site uses dynamic JS, but HTML can be fetched; alternatively use their RSS feeds or JSON endpoints if any). We need to collect all listings (the site has genre/category pages).
- **Webnovel:** If no public API, use an account and their Inkstone portal; possibly emulate login and fetch data (site might be dynamic). Otherwise rely on web scraping or use webnovel’s suggestion system or published lists of trending series.
- **Webtoon & Tapas:** These sites are mostly client-heavy, but the mobile web versions often have static pages. We can scrape:
    - Webtoon: the mobile site (m.webtoons.com) is simpler, or use the Web API (if reverse-engineered). Data needed: series name, authors, genre, like/view stats.
    - Tapas: scrape tapas.io by genre pages or search API (if exists).
    - MangaDex: use the **MangaDex API v5** (documented on GitLab) to query top followed/viewed manga. It supports filtering by language and source.
- **Other sources:** If analyzing *anime popularity* as context, we could use MyAnimeList or AniList APIs, but primary focus is story content, so optional.

For **Scraping Tools**, we will use Python (Requests, BeautifulSoup, Selenium only if needed), and manage a crawl database to avoid repeats.  APIs will be accessed via HTTP with rate limiting.  We should respect each site’s terms of service (AO3 allows non-commercial scraping under CC-BY-NC-SA; others may have restrictions).

**Data storage:**  Use a relational or NoSQL database to store records of works, authors, and time-series of stats.  Key indices: by platform, by fandom/genre, by author.  This allows queries like “top-100 works in genre X” or “top fandoms by total hits”.  Also prepare for large scale: e.g. AO3 has ~10M works, so initial crawls may sample or focus on top lists only.

**Analysis Plan:**  With the data collected, analytics can include:

- **Popularity ranking:** Identify the *most popular works and fandoms* (by hits/kudos). E.g. list top 50 fanfic per fandom.
- **Genre/Tag trends:** See which tags/genres correlate with high engagement. The Statsignificant analysis gives clues (celebrity fanfic, romance).
- **Length vs. popularity:** Correlate chapter/word counts with views. The user specifically asked for “top 100 word count, number of hits, bookmarks, kudos etc.” — so we will compute distributions.
- **Serialization patterns:** Use chapter-level counts to analyze writing pace (words per chapter, updates frequency) for successful serials.
- **Pairings/characters:** Extract and tally most common relationships and characters (e.g., “ships” in popular fandoms).
- **International analysis:** As data permits, compare English fanfic vs. translations or non-English user content (language field).
- **Creator earnings:** Though raw earnings are private, we can glean from Patreon/Ko-fi pages or public reports which creators earn significantly (e.g. top Patreon fiction creators) and link that back to their works/popularity.
- **Market positioning:** Use traffic stats (SimilarWeb data ) to prioritize focus (AO3/Wattpad > FanFiction.net, for instance).

By building this dataset and framework, one can later run detailed queries or machine learning models to detect trends, seasonal changes, or predict what genres/themes are likely to succeed.  The output for now is a clear blueprint: **scrape the platforms above for the fields listed, store them in a database, and then run analytics on fandom/genre popularity, content features, and creator monetization**.

## **Tools, APIs, and Services**

- **Official/Public APIs:** Wattpad (public developer API, v4) for stories ; MangaDex (public REST API v5); Webnovel (may have private API via Inkstone); possibly MyAnimeList/Anilist (for anime as background).
- **Unofficial libraries:** The ao3 Python package for AO3 scraping; any community libraries for RoyalRoad or Webtoons (less common).
- **Web scraping:** Custom Python scripts (requests/BeautifulSoup) and possibly Selenium for dynamic sites. Ensure moderate request rates, use cache, and parse HTML for the desired fields.
- **Data aggregation:** Consider using Kaggle/open datasets where available (there are AO3 dumps【51†】, RoyalRoad stats analyses , etc.) to bootstrap.
- **Analysis tools:** Pandas/NumPy for data processing; SQL (or NoSQL) for querying large tables; visualization libraries for charts.

## **Summary**

This plan outlines the **scope of platforms** (AO3, FFN, Wattpad, RoyalRoad, Webnovel, Webtoon, Tapas, MangaDex, etc.), **data fields** (titles, fandoms, tags, words, chapters, hits, likes, comments, etc.), and **collection methods** (APIs and scraping) needed for a comprehensive market analysis of fanfiction, light novels, manga/webtoons, and related media.  By assembling this data, we can identify *which worlds and genres are most popular*, *what story lengths and formats readers engage with*, and *how creators currently monetize*.  This will inform where an AI-powered writing startup should focus initial efforts.  All cited sources reflect current market data and industry insights    , guiding the analytics strategy.

**Sources:** Industry reports and site analytics    ; platform documentation and developer discussions   ; community research (AO3 stats, surveys)   .  (Image source: Persistence Market Research .)