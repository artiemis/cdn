module.exports = {
	apps: [
		{
			name: 'cdn',
			script: 'env/bin/python',
			args: '-m hypercorn main:app --bind "0.0.0.0:5000" --access-logfile -',
		},
	],
};
