var express = require('express');
var router = express.Router();
var _heroes = require('../public/json/heroes.json')
var Prediction = require('../models/Prediction')


_heroes = _heroes.sort((a, b) => {
  if (a.localized_name < b.localized_name) { return -1; }
  if (a.localized_name > b.localized_name) { return 1; }
  return 0;
});

_heroes.get = function (hero_id) {
  return this.filter((e) => e.id == hero_id)[0];
}

/* GET home page. */
router.get('/', function (req, res, next) {
  res.render('index', { title: 'Dota lineup prediction', heroes: _heroes });
});

router.post('/', function (req, res, next) {
  const id = Prediction.getId(req.body);
  let prediction = Prediction.findOne(id);
  if (prediction === null) {
    prediction = Prediction.create(req.body);
    if (prediction)
      res.render('index', { title: 'Dota lineup prediction', heroes: _heroes, prediction: prediction });
  }
  else {
    res.render('response', { title: 'Prediction result', heroes: _heroes, prediction: prediction });
  }
})

module.exports = router;
