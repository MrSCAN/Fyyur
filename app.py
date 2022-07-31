#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from email.policy import default
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models.models import Artist, Show, Venue,db
import datetime



#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
db.init_app(app)

moment = Moment(app)
app.config.from_object('config')


# TODO: connect to a local postgresql database
migrate = Migrate(app, db) # this


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
      date = dateutil.parser.parse(value)
  else:
      date = value
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  venues = db.session.query(Venue).group_by(Venue.id, Venue.city, Venue.state).all()
 
  data = []
  # for venue in venues
  for venue_obj in venues:
    upcoming_shows = 0
    shows = venue_obj.show
    for show in shows:
      if show.start_time > datetime.datetime.now():
            upcoming_shows += 1
    if any(x['state'] == venue_obj.state  for x in data) and any(x['city'] == venue_obj.city  for x in data):
        index = next((i for i, item in enumerate(data) if item['state'] == venue_obj.state and item['city'] == venue_obj.city), -1)
        data[index]['venues'].append(
          {
          "id": venue_obj.id,
          "name": venue_obj.name,
          "num_upcoming_shows": upcoming_shows
          }
        )
    else:
      data.append({
          "city": venue_obj.city,
          "state": venue_obj.state,
          "venues" : [{
          "id": venue_obj.id,
          "name": venue_obj.name,
          "num_upcoming_shows": upcoming_shows
          }]
        })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():

  data = []
  q = request.form.get('search_term').lower()
  venues = Venue.query.filter(Venue.name.ilike('%' + q + '%'))


  for venue in venues:
    upcoming_shows = 0
    shows = venue.show
    for show in shows:
      if show.start_time > datetime.datetime.now():
            upcoming_shows += 1

    data.append({
      "id" : venue.id,
      "name" : venue.name,
      "num_upcoming_shows" : upcoming_shows
    })


  data = {
    "count": venues.count(),
    "data" : data
  }

  return render_template('pages/search_venues.html', results=data, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue = Venue.query.get(venue_id)

  if  venue:
    venue.genres = list(venue.genres.replace('}', '').replace('{', '').split(','))
  

  return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  name = request.form.get('name')
  city = request.form.get('city')
  state = request.form.get('state')
  address = request.form.get('address')
  phone = request.form.get('phone')
  genres = request.form.getlist('genres')
  facebook_link = request.form.get('facebook_link')
  image_link = request.form.get('image_link')
  website_link = request.form.get('website_link')
  seeking_talent = request.form.get('seeking_talent')
  seeking_description = request.form.get('seeking_description')
  venue = Venue(name=name, city=city, state=state, address=address, phone=phone,
           genres=genres, facebook_link=facebook_link, image_link=image_link, website_link=website_link,
            seeking_talent=seeking_talent, seeking_description=seeking_description )

  error = False
  try:
    db.session.add(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if not error:

    flash('Venue  ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')
  else:
    #Flash error when there is error as well
    flash('An error occured ' + request.form['name'] + ' was not Added!', 'error')
    return render_template('forms/edit_venue.html', form=VenueForm(), venue=venue)



  
  

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  error = False
  try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
  except:
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  if error:
      return jsonify({'success': False})
  else:
    return jsonify({'success': True})
      

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  data = Artist.query.order_by('id').all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  data = []
  q = request.form.get('search_term')
  artists = Artist.query.filter(Artist.name.ilike('%' + q + '%'))


  for artist in artists:
    upcoming_shows = 0
    shows = artist.show
    for show in shows:
      if show.start_time > datetime.datetime.now():
            upcoming_shows += 1
    data.append({
      "id" : artist.id,
      "name" : artist.name,
      #TODO
      "num_upcoming_shows" : upcoming_shows
    })


  data = {
    "count": artists.count(),
    "data" : data
  }

  return render_template('pages/search_artists.html', results=data, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  data = []
  past_shows = []
  upcoming_shows = []
  artists = db.session.query(
         Artist
    ).all()

  for artist in artists:
    shows = artist.show
    for show in shows:
      venue = Venue.query.get(show.venue_id)

      if show.start_time > datetime.datetime.now():
          upcoming_shows.append({
            "venue_id":venue.id, 
            "venue_name":venue.name,
            "venue_image_link":venue.image_link,
            "start_time":show.start_time
          })
      else:
          past_shows.append({
            "venue_id":venue.id, 
            "venue_name":venue.name,
            "venue_image_link":venue.image_link,
            "start_time":show.start_time
          })
    data = {
      "id": artist.id,
      "name": artist.name,
      "genres": list(artist.genres.replace('}', '').replace('{', '').split(',')),    
      "city": artist.city,
      "state":artist.state,
      "phone": artist.phone,
      "website": artist.website_link,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,    
      "seeking_description": artist.seeking_description,
      "image_link":artist.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)

    }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist = Artist.query.get(artist_id)
  form.name.data = artist.name
  form.genres.data = artist.genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website_link
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  artist = Artist.query.get(artist_id)
  artist.id = artist_id
  artist.name = request.form.get('name')
  artist.city = request.form.get('city')
  artist.state = request.form.get('state')
  artist.phone = request.form.get('phone')
  artist.genres = request.form.getlist('genres')
  artist.facebook_link = request.form.get('facebook_link')
  artist.image_link = request.form.get('image_link')
  artist.website_link = request.form.get('website_link')
  artist.seeking_venue = request.form.get('seeking_venue')
  artist.seeking_description = request.form.get('seeking_description')

  error = False
  try:
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if not error:
    flash('Artist ' + request.form.get('name') + ' was successfully updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))
  else:
    flash('An error occurred. Artist ' + request.form.get('name') + ' could not be updated.')
    return render_template('forms/edit_artist.html', form=ArtistForm(), artist=artist)

  

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  venue = Venue.query.get(venue_id)

  form.name.data = venue.name
  form.genres.data = venue.genres
  form.address.data = venue.address
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.website_link.data = venue.website_link
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link


  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  
  venue = Venue.query.get(venue_id)
  venue.id = venue_id
  venue.name = request.form.get('name')
  venue.city = request.form.get('city')
  venue.state = request.form.get('state')
  venue.address = request.form.get('address')
  venue.phone = request.form.get('phone')
  venue.genres = request.form.getlist('genres')
  venue.facebook_link = request.form.get('facebook_link')
  venue.image_link = request.form.get('image_link')
  venue.website_link = request.form.get('website_link')
  venue.seeking_talent = request.form.get('seeking_talent')
  venue.seeking_description = request.form.get('seeking_description')

  # TODO: insert form data as a new Venue record in the db, instead
  error = False
  try:
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if not error:
    flash('Venue  ' + request.form['name'] + ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))
  else:
    #Flash error when there is error as well
    flash('An error occured ' + request.form['name'] + ' was not updated!', 'error')
    return render_template('forms/edit_venue.html', form=VenueForm(), venue=venue)
  
  

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  name = request.form.get('name')
  city = request.form.get('city')
  state = request.form.get('state')
  phone = request.form.get('phone')
  genres = request.form.getlist('genres')
  facebook_link = request.form.get('facebook_link')
  image_link = request.form.get('image_link')
  website_link = request.form.get('website_link')
  seeking_venue = request.form.get('seeking_venue')
  seeking_description = request.form.get('seeking_description')

  artist = Artist(name=name, city=city, state=state, phone=phone,
           genres=genres, facebook_link=facebook_link, image_link=image_link, website_link=website_link,
            seeking_venue=seeking_venue, seeking_description=seeking_description )

  error = False
  try:
    db.session.add(artist)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if not error:
    flash('Artist ' + name + ' was successfully listed!')
    return render_template('pages/home.html')
  else:
    flash('An error occurred. Artist ' + name + ' could not be listed.')
    return render_template('forms/edit_artist.html', form=ArtistForm(), artist=artist)



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  shows = db.session.query(Show.start_time, Show.artist_id, Show.venue_id, Artist.name, Artist.image_link, Venue.name).join(Artist).join(Venue).all()
  for show in shows:
    data.append({
      "venue_id": show[2],
      "venue_name": show[5],
      "artist_id": show[1],
      "artist_name": show[3],
      "artist_image_link": show[4],
      "start_time": show[0]
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  start_time = request.form.get('start_time')
  artist_id = request.form.get('artist_id')
  venue_id = request.form.get('venue_id')

  artist = Artist.query.get(artist_id)
  venue = Venue.query.get(venue_id)

  if(not artist):
    flash("There is no artist with id "+artist_id, "error")
    return render_template('forms/new_show.html', form=ShowForm())
  if(not venue):
    flash("There is no venue with id "+venue_id, "error")
    return render_template('forms/new_show.html', form=ShowForm())

  

  show = Show(start_time=start_time, artist_id=artist_id, venue_id=venue_id)

  # TODO: insert form data as a new Venue record in the db, instead
  error = False

  try:
    db.session.add(show)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if not error:
    flash('Show was successfully listed!')
    return render_template('pages/home.html')
  else:
    flash('An error occurred. Show could not be listed.', "error")
    return render_template('forms/new_show.html', form=ShowForm())

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#
# Default port:
if __name__ == '__main__':
    app.debug = True
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
