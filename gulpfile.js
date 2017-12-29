var gulp = require('gulp');
var browserSync = require('browser-sync');
var sass = require('gulp-sass');
var sourcemaps = require('gulp-sourcemaps');
var autoprefixer = require('gulp-autoprefixer');
var cleanCSS = require('gulp-clean-css');
var uglify = require('gulp-uglify');
var concat = require('gulp-concat');
var imagemin = require('gulp-imagemin');
var changed = require('gulp-changed');
var htmlReaplce = require('gulp-html-replace');
var htmlMin = require('gulp-htmlmin');
var del = require('del');
var sequence = require('run-sequence');
var minifyInline = require('gulp-minify-inline');
var gulpCopy = require('gulp-copy');

let target = './backend/static/';
var config = {
  dist: target,
  watch: 'web/**/*.{html,css,js.jpg,jpeg,png,gif.svg}',
  src: 'web/',
  cssin: 'web/**/*.css',
  jsin: 'web/**/*.js',
  jsinlibs: 'web/scripts/*.js',
  imgin: 'web/img/**/*.{jpg,jpeg,png,gif,svg}',
  htmlin: 'web/**/*.html',
  scssin: 'web/**/*.scss',
  cssout: target + '',
  jsout: target  + '',
  imgout: target + 'img/',
  htmlout: target + '',
  jsoutlibs: target + 'scripts/',
  scssout: 'web/',
  cssoutname: 'styles.css',
  jsoutname: 'dist.js',
  cssreplaceout: 'web/dist-style.css',
  jsreplaceout: 'web/dist-script.js'
};

gulp.task('reload', function() {
  browserSync.reload();
});

gulp.task('serve', ['sass'], function() {
  browserSync({
    server: config.src
  });
  
  gulp.watch([config.htmlin, config.jsin], ['reload']);
  gulp.watch(config.scssin, ['sass']);

});

gulp.task('sass', function() {
  return gulp.src(config.scssin)
             .pipe(sourcemaps.init())
             .pipe(sass().on('error', sass.logError))
             .pipe(autoprefixer({
               browsers: ['last 3 versions']
             }))
             .pipe(sourcemaps.write())
             .pipe(gulp.dest(config.scssout))
             .pipe(browserSync.stream());
});

gulp.task('css', function() {
  return gulp.src(config.cssin)
             .pipe(concat(config.cssoutname))
             .pipe(cleanCSS())
             .pipe(gulp.dest(config.cssout));
});

gulp.task('js', function() {
  return gulp.src(config.jsin)
             .pipe(concat(config.jsoutname))
             .pipe(uglify())
             .pipe(gulp.dest(config.jsout));
});

gulp.task('copy-js-libs', function(){
  return  gulp.src(config.jsinlibs)
              .pipe(gulp.dest(config.jsoutlibs));
});

gulp.task('img', function() {
  return gulp.src(config.imgin)
             .pipe(changed(config.imgout))
             .pipe(imagemin())
             .pipe(gulp.dest(config.imgout));
});

gulp.task('html', function() {
  return gulp.src(config.htmlin)
             .pipe(htmlReaplce({
               'css': config.cssreplaceout,
               'js': config.jsreplaceout
             }))
             .pipe(minifyInline())
             .pipe(htmlMin({
               sortAttributes: true,
               sortClassName: true,
               collapseWhitespace: true
             }))
             .pipe(gulp.dest(config.dist))
});

gulp.task('clean', function() {
  return del([config.dist]);
});

gulp.task('watch', function() {
  sequence('build');

  var watcher = gulp.watch(config.watch, ['html', 'js', 'copy-js-libs', 'css', 'img']);
  watcher.on('change', function(event) {
    console.log('File ' + event.path + ' was ' + event.type + ', running tasks...');
  });
});

gulp.task('build', function() {
  sequence('clean', ['html', 'js', 'copy-js-libs', 'css', 'img']);
});


gulp.task('default', ['serve']);
