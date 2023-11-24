function _make_figures(plot_dir, plot_format)
    ids_array=winsid();
    for i=1:length(ids_array)
      id=ids_array(i);
      outfile = sprintf('%s/__ipy_sci_fig_%03d', plot_dir, i);
      if plot_format == 'jpg' then
        xs2jpg(id, outfile + '.jpg');
      elseif plot_format == 'jpeg' then
        xs2jpg(id, outfile + '.jpeg');
      elseif plot_format == 'png' then
        xs2png(id, outfile);
      else
        xs2svg(id, outfile);
      end
      close(id);
    end
 endfunction