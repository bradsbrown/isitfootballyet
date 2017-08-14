
function football() {
    this.init = function(a) {

		var q = new Date();
        var m = q.getMonth();
        var d = q.getDate();
        var y = q.getFullYear();
        var today = new Date(y, m, d);
        var fball = document.getElementById("football");

        var games;

        $.ajax({
            type: 'GET',
            url: 'football.json',
            async: false,
            dataType: 'json',
            success: function(data) {
                games = data;
            },
            error: function(data) {
                json = data.responseJSON;
            }
        });

        for (var i = 0; i < games.length; i++) {
            var game = games[i];

            dt = new Date(game.date);

            var tzoffset = -1 * (new Date()).getTimezoneOffset() * 60000; //offset in milliseconds
            fbegin = (new Date(dt - tzoffset))

            if (today <= fbegin) {
                // alert(game.id);
                // fbegin=(new Date(dt - tzoffset))
                break;
            }
        }


        // alert(fbegin);



        // fbegin=new Date(2016,10,02,18,30);
        fend = new Date('2017-01-02');

        fball.innerHTML = 'NO';

        if (today >= fbegin && today <= fend) {
            fball.innerHTML = 'YES'
            document.getElementById('timer').style.display = 'none';
            document.getElementById('countdown').style.display = 'none';
        } else {
            fball.innerHTML = 'NO';
			countdown.init('timer',fbegin)

        }

    }
}

function countdown() {
	this.init = function(div,endtime) {
		// alert(div)
		// alert(endtime)
		// alert(this.timeRemaining(endtime).weeks);

		var timer = document.getElementById(div);
		this.outputTime(div,endtime);
		var timeinterval = setInterval(function(){
    		countdown.outputTime(div,endtime);
            var t = countdown.timeRemaining(endtime);
			if(t.total<=0){
				clearInterval(timeinterval);
			}
		},1000);

    }
	this.timeRemaining = function(endtime){
		// alert(endtime)
		var t = Date.parse(endtime) - Date.parse(new Date());
		var s = Math.floor( (t/1000) % 60 );
		var m = Math.floor( (t/1000/60) % 60 );
		var h = Math.floor( (t/(1000*60*60)) % 24 );
		var d = Math.floor( t/(1000*60*60*24) % 7 );
		var w = Math.floor( t/(1000*60*60*24*7) );
		// alert(w);
		return {
			'total': t,
			'weeks': w,
			'days': d,
			'hours': h,
			'minutes': m,
			'seconds': s
		};
	}

	this.outputTime = function(div,endtime){
		var t = countdown.timeRemaining(endtime);
		var html = '<table>';

		if(t.weeks==1){
			html = html + '<tr><td class=\'right\'>' + ('0' + t.weeks).slice(-2) + '</td><td class=\'left\'>  week</tr>';
		}else if (t.weeks>1) {
			html = html + '<tr><td class=\'right\'>' + ('0' + t.weeks).slice(-2) + '</td><td class=\'left\'>  weeks</tr>';
		}

		if(t.days==1){
			html = html + '<tr><td class=\'right\'>' + ('0' + t.days).slice(-2) + '</td><td class=\'left\'>  day</tr>';
		}else if (t.days>1||t.weeks>1) {
			html = html + '<tr><td class=\'right\'>' + ('0' + t.days).slice(-2) + '</td><td class=\'left\'>  days</tr>';
		}

		if(t.hours==1){
			html = html + '<tr><td class=\'right\'>' + ('0' + t.hours).slice(-2) + '</td><td class=\'left\'  hour</tr>';
		}else if (t.hours>1||t.days>1) {
			html = html + '<tr><td class=\'right\'>' + ('0' + t.hours).slice(-2) + '</td><td class=\'left\'>  hours</tr>';
		}

		if(t.minutes==1){
			html = html + '<tr><td class=\'right\'>' + ('0' + t.minutes).slice(-2) + '</td><td class=\'left\'>  minute</tr>';
		}else if (t.minutes>1||t.hours>1) {
			html = html + '<tr><td class=\'right\'>' + ('0' + t.minutes).slice(-2) + '</td><td class=\'left\'>  minutes</tr>';
		}

		if(t.seconds==1){
			html = html + '<tr><td class=\'right\'>' + ('0' + t.seconds).slice(-2) + '</td><td class=\'left\'>second</tr>';
		}else if (t.seconds>1||t.minutes>1) {
			html = html + '<tr><td class=\'right\'>' + ('0' + t.seconds).slice(-2) + '</td><td class=\'left\'>seconds</tr>';
		}

		html = html + '</table>';

		// timer.innerHTML = t.days + ' days<br>' +
		//                   t.hours + ' hours<br>' +
		//                   t.minutes + ' minutes<br>' +
		//                   t.seconds + ' seconds';

		timer.innerHTML = html;
	}

}

var football = new football
var countdown = new countdown
