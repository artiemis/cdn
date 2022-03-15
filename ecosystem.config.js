module.exports = {
	apps: [
		{
			name: 'yuzu',
			script: 'env/bin/python',
			args: '-m uvicorn main:app --port 5000',
		},
	],
};
