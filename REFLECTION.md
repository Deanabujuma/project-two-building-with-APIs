# Project #2: HTTP.tv

## Reflection

### 1. API Research and Provider Selection

For this project, I decided to create a TV show tracking application
using TVmaze. I wanted to create something that I would actually find
useful and something that could be visually interesting. I liked the
idea of being able to search for shows, save them, and keep track of
what season or episode I was on.

During the research process, I compared different APIs and learned
that they don't all provide the same information or have the same
requirements. TVmaze stood out because it didn't require an API key
and provided information such as show names, posters, genres, and
networks.

One thing I hadn't really considered before this project was
licensing. I learned that even when information is available through
an API, there can still be rules about how that information is used
and shared. ShareAlike was something I needed to look into because
I hadn't previously thought much about the difference between using
someone else's data and storing my own information.

### 2. Prototype and Design Decisions

One of the biggest decisions I made was how I wanted the application
to look. I looked at three different layouts before choosing Direction
D, which was more similar to a streaming platform.

I preferred Direction D because the other layouts felt more like
regular websites or lists. I wanted HTTP.tv to feel like an actual
TV application, with larger images, a darker background, and an
organized way to view show information.

One of the changes during prototyping was removing streaming
providers that couldn't be verified through TVmaze. This showed
me that I couldn't just include something because it looked good.
I needed to make sure the information being displayed was accurate.

I also learned that prototyping is useful because I can compare
different ideas before deciding what to implement. Instead of
immediately starting with one design, I could see what worked
and what needed to change.

### 3. Understanding the API Request and Response

This is one of the areas I still need to go back and review because
I don't fully understand every part of the process yet.

One thing I worked on understanding was the difference between
using an external API and creating my own API. HTTP.tv gets show
information from TVmaze, but it also provides its own API for
reading and updating information stored in the application.

For example, the second Python script uses the API to update
a show's progress. The next command first requests the saved
information through GET, then sends a PATCH request to update
the episode number.

I learned that an API request doesn't automatically mean the
database will change. The application first checks whether the
user has permission to access the information and whether the
new values are valid.

Something I found interesting was that the same information
can be checked in multiple places, including the model,
serializer, and database. I still need more practice tracing
the entire process from the Python script to Django and back,
but I have a better idea of why those steps are necessary.

### 4. Search, Filtering, Sorting, and Pagination

Before working on this project, I didn't have a strong
understanding of how searching, filtering, sorting, and
pagination were different.

I learned that searching looks for matching information,
filtering narrows down the results based on certain conditions,
sorting determines the order, and pagination divides the
results into smaller pages.

In HTTP.tv, the collection can be filtered by watching status,
and the API can also filter by information such as rating,
genre, and network. The results can be sorted, and pagination
prevents the application from displaying everything at once.

One issue that came up was how to handle shows that didn't have
a rating. I learned that the database doesn't automatically
sort those entries the way I might expect, so the application
needed additional logic to keep unrated shows at the end.

If HTTP.tv eventually had thousands of entries, I would want
to improve how quickly the application searches and loads
information. I would look into a database better suited for
a larger application, such as PostgreSQL, and ways to make
searching and loading images more efficient.

### 5. Bugs, Corrections, and Lessons Learned

One of the biggest things I learned from this project was that
passing automated tests doesn't always mean everything will
look or work correctly when using the actual application.

During development, some issues only became noticeable when
working with real TVmaze information. For example, shows with
similar names needed additional details to tell them apart,
and some background images already had text included in them.

Another issue involved validating the season and episode
fields. The application needed to make sure that both values
were provided together or both were left empty. This helped
show why testing different situations matters instead of
only checking whether something works under normal conditions.

The project also involved correcting differences between how
the web form and API handled certain errors. I learned that
even when two parts of an application do similar things, they
still need to follow the same rules.

If I were starting this project again, I would spend more time
understanding each part before moving to the next. I would
also test with real information earlier and review the code
more often rather than relying only on passing tests.

I still have a lot to review, especially Django views,
serializers, database models, and how API requests move through
the application. However, this project gave me a better idea
of how those parts connect and what I need to focus on learning
before my Design Defense.
