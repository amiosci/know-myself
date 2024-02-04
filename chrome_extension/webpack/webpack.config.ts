import path from 'path';
import webpack from 'webpack';
import CopyPlugin from 'copy-webpack-plugin';

const repoRoot = path.join(__dirname, '/..')

const config: webpack.Configuration = {
    mode: 'development',
    target: 'web',
    entry: {
        app: './src/app/app.ts',
        popup: './src/popup/popup.ts',
        service_worker: './src/service_worker/worker.ts',
        recorder: './src/recorder.ts',
    },
    module: {
        rules: [
            {
                test: /\.ts$/,
                use: 'ts-loader',
                exclude: /node_modules/,
            },
        ],
    },
    resolve: {
        extensions: [
            '.ts',
            '.js'
        ],
    },
    output: {
        path: path.resolve(repoRoot, 'dist'),
    },
    plugins: [
        new CopyPlugin({
            patterns: [
                {
                    from: 'node_modules/smart-webcomponents-community/source/styles/font',
                    to: './font',
                },
                {
                    from: 'node_modules/@shoelace-style/shoelace/dist',
                    to: './shoelace_dist',
                },
                {
                    from: 'node_modules/smart-webcomponents-community/source/styles/smart.default.css',
                    to: './smart-webcomponents.css'
                },
                {
                    from: 'node_modules/@shoelace-style/shoelace/dist/shoelace.js',
                    to: '.'
                },
                {
                    from: 'html/*.html',
                    // copy to output root
                    to({ context, absoluteFilename }) {
                        return "./[name][ext]";
                    },
                },
                {
                    from: 'src/manifest.json',
                    to: '.'
                }
            ]
        })
    ]
};

export default config;
