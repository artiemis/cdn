module.exports = {
	apps: [
		{
			name: 'cdn',
			script: 'env/bin/python',
			args: '-m uvicorn main:app --port 5000',
		},
	],
};
