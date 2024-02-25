import path from 'path';
import webpack from 'webpack';
import CopyPlugin from 'copy-webpack-plugin';

const repoRoot = path.join(__dirname, '/..')

const config: webpack.Configuration = {
    mode: 'development',
    watch: true,
    target: 'web',
    devtool: 'cheap-source-map',
    entry: {
        app: './src/app.ts',
        popup: './src/popup.ts',
        service_worker: './src/worker.ts',
        recorder: './src/recorder.ts',
        shoelace: './node_modules/@shoelace-style/shoelace/dist/shoelace.js'
    },
    module: {
        rules: [
            {
                test: /\.ts$/,
                use: 'ts-loader',
                exclude: /node_modules/,
            },
            {
                test: /\.(sa|sc|c)ss$/,
                use: ["style-loader", "css-loader", "sass-loader"]
            }
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
        // Bundle absolute resource paths in the source-map,
        // so VSCode can match the source file.
        devtoolModuleFilenameTemplate: '[absolute-resource-path]'
    },
    plugins: [
        new CopyPlugin({
            patterns: [
                {
                    from: 'node_modules/@shoelace-style/shoelace/dist',
                    to: './shoelace_dist',
                },
                {
                    from: 'html/*.html',
                    // copy to output root
                    to({ context, absoluteFilename }) {
                        return "./[name][ext]";
                    },
                },
                {
                    from: 'config/*.*',
                    // copy to output root
                    to({ context, absoluteFilename }) {
                        return "./[name][ext]";
                    },
                },
            ]
        })
    ]
};

export default config;
